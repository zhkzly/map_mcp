
import asyncio
import logging
import os
import shutil
from contextlib import AsyncExitStack
from datetime import timedelta
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client
from mcp.client.sse import sse_client



class Tool:
    """Represents a tool with its properties and formatting."""

    def __init__(
        self, name: str, description: str, input_schema: dict[str, Any]
    ) -> None:
        self.name: str = name
        self.description: str = description
        self.input_schema: dict[str, Any] = input_schema

    def format_for_llm(self) -> str:
        """Format tool information for LLM.

        Returns:
            A formatted string describing the tool.
        """
        args_desc = []
        if "properties" in self.input_schema:
            for param_name, param_info in self.input_schema["properties"].items():
                arg_desc = (
                    f"- {param_name}: {param_info.get('description', 'No description')}"
                )
                if param_name in self.input_schema.get("required", []):
                    arg_desc += " (required)"
                args_desc.append(arg_desc)

        return f"""
Tool: {self.name}
Description: {self.description}
Arguments:
{chr(10).join(args_desc)}
"""
    
    
# TODO:这里主要是如何连接调用server
# 1.通信类型：stdio用于本地进程，HTTP/SSE用于远程服务器
# 2.认证：HTTP/SSE传输支持Bearer token认证，用于保护服务器访问
# 3.会话管理：HTTP支持会话持久化，SSE支持服务器推送消息
# 4.如何管理多个server的连接，支持同时连接多个不同类型的server

class BaseServer:
    """Manages MCP server connections and tool execution."""
    def __init__(self, name: str, config: dict[str, Any]) -> None:
        self.name: str = name
        self.config: dict[str, Any] = config

        self.session: ClientSession | None = None
        self._cleanup_lock: asyncio.Lock = asyncio.Lock()
        self.exit_stack: AsyncExitStack = AsyncExitStack()
        self.server_type: str|None=None 

    async def initialize(self) -> None:
        """Initialize the server connection."""
        raise NotImplementedError("Subclasses should implement this method.")

    async def list_tools(self) -> list[Any]:
        """List available tools from the server.

        Returns:
            A list of available tools.

        Raises:
            RuntimeError: If the server is not initialized.
        """
        if not self.session:
            raise RuntimeError(f"Server {self.name} not initialized")

        tools_response = await self.session.list_tools()
        tools = []

        for item in tools_response:
            if isinstance(item, tuple) and item[0] == "tools":
                tools.extend(
                    Tool(tool.name, tool.description, tool.inputSchema)
                    for tool in item[1]
                )

        return tools

    async def execute_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        retries: int = 2,
        delay: float = 1.0,
    ) -> Any:
        """Execute a tool with retry mechanism.

        Args:
            tool_name: Name of the tool to execute.
            arguments: Tool arguments.
            retries: Number of retry attempts.
            delay: Delay between retries in seconds.

        Returns:
            Tool execution result.

        Raises:
            RuntimeError: If server is not initialized.
            Exception: If tool execution fails after all retries.
        """
        if not self.session:
            raise RuntimeError(f"Server {self.name} not initialized")

        attempt = 0
        while attempt < retries:
            try:
                logging.info(f"Executing {tool_name}...")
                result = await self.session.call_tool(tool_name, arguments)

                return result

            except Exception as e:
                attempt += 1
                logging.warning(
                    f"Error executing tool: {e}. Attempt {attempt} of {retries}."
                )
                if attempt < retries:
                    logging.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logging.error("Max retries reached. Failing.")
                    raise

    async def cleanup(self) -> None:
        """Clean up server resources."""
        async with self._cleanup_lock:
            try:
                await self.exit_stack.aclose()
                self.session = None
                self.stdio_context = None
            except Exception as e:
                logging.error(f"Error during cleanup of server {self.name}: {e}")


class StdioServer(BaseServer):
    """Manages MCP server connections and tool execution."""

    def __init__(self, name: str, config: dict[str, Any]) -> None:
        super().__init__(name, config)
        self.stdio_context: Any | None = None
        self.server_type = "stdio"
        

    async def initialize(self) -> None:
        """Initialize the server connection."""
        command = (
            shutil.which("npx")
            if self.config["command"] == "npx"
            else self.config["command"]
        )
        if command is None:
            raise ValueError("The command must be a valid string and cannot be None.")

        server_params = StdioServerParameters(
            command=command,
            args=self.config["args"],
            env={**os.environ, **self.config["env"]}
            if self.config.get("env")
            else None,
        )
        try:
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            read, write = stdio_transport
            session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )
            await session.initialize()
            self.session = session
        except Exception as e:
            logging.error(f"Error initializing server {self.name}: {e}")
            await self.cleanup()
            raise

class StreamableHttpServer(BaseServer):
    """Manages MCP server connections over StreamableHTTP transport."""
    def __init__(self, name: str, config: dict[str, Any]) -> None:
        super().__init__(name, config)
        self.server_type = "streamable-http"

    async def initialize(self) -> None:
        """Initialize the server connection over StreamableHTTP protocol."""
        if not self.config.get("url"):
            raise ValueError("URL must be provided for StreamableHTTP transport")

        url = self.config["url"]
        
        # 准备可选的headers和认证参数
        headers = self.config.get("headers", {})
        timeout = timedelta(seconds=self.config.get("timeout", 30))
        sse_read_timeout = timedelta(seconds=self.config.get("sse_read_timeout", 300))
        terminate_on_close = self.config.get("terminate_on_close", True)
        
        # 如果配置中有API key，添加为Bearer token
        auth = None
        if self.config.get("api_key"):
            # 使用httpx的Auth接口
            # import httpx
            # auth = httpx.Auth()
            # 或者简单地添加到headers中
            headers["Content-Type"] = "application/json"
            # headers["Authorization"] = f"Bearer {self.config['api_key']}"

        try:
            # 使用正确的参数名和签名创建StreamableHTTP客户端
            transport = await self.exit_stack.enter_async_context(
                streamablehttp_client(
                    url=url,
                    headers=headers,
                    timeout=timeout,
                    sse_read_timeout=sse_read_timeout,
                    terminate_on_close=terminate_on_close,
                    # auth=auth,
                )
            )
            
            # streamablehttp_client返回三个值：read_stream, write_stream, get_session_id
            read_stream, write_stream, get_session_id = transport
            
            # 创建会话并初始化
            session = await self.exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            await session.initialize()
            self.session = session
            
            # 记录session ID（如果可用）
            if get_session_id:
                session_id = get_session_id()
                if session_id:
                    logging.info(f"Connected to StreamableHTTP server {self.name} with session ID: {session_id}")
            
        except Exception as e:
            logging.error(f"Error initializing StreamableHTTP server {self.name}: {e}")
            await self.cleanup()
            raise

class SseServer(BaseServer):
    """Manages MCP server connections over SSE transport."""
    def __init__(self, name: str, config: dict[str, Any]) -> None:
        super().__init__(name, config)
        self.server_type = "sse"

    async def initialize(self) -> None:
        """Initialize the server connection over SSE protocol."""
        if not self.config.get("url"):
            raise ValueError("URL must be provided for SSE transport")
            
        url = self.config["url"]
        
        # 准备可选的headers和认证参数
        headers = self.config.get("headers", {})
        timeout = self.config.get("timeout", 5)
        sse_read_timeout = self.config.get("sse_read_timeout", 300)
        
        # 如果配置中有API key，添加为Bearer token
        auth = None
        if self.config.get("api_key"):
            # 使用httpx的Auth接口或添加到headers中
            # headers["Authorization"] = f"Bearer {self.config['api_key']}"
            headers["Content-Type"] = "application/json"
        
        try:
            # 使用正确的参数创建SSE客户端
            transport = await self.exit_stack.enter_async_context(
                sse_client(
                    url=url,
                    headers=headers,
                    timeout=timeout,
                    sse_read_timeout=sse_read_timeout,
                    auth=auth,
                )
            )

            # sse_client返回两个值：read_stream, write_stream
            read_stream, write_stream = transport

            # 创建会话并初始化
            session = await self.exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            await session.initialize()
            self.session = session
            
        except Exception as e:
            logging.error(f"Error initializing SSE server {self.name}: {e}")
            await self.cleanup()
            raise


def create_server(name: str, config: dict[str, Any]) -> BaseServer:
    """Factory function to create appropriate server based on configuration.
    
    Args:
        name: Name for the server instance
        config: Server configuration dictionary with transport type
        
    Returns:
        An instance of appropriate Server subclass
        
    Raises:
        ValueError: If transport type is not supported
    """
    transport = config.get("transport", "stdio")
    
    if transport == "stdio":
        return StdioServer(name, config)
    elif transport == "streamable-http":
        return StreamableHttpServer(name, config)
    elif transport == "sse":
        return SseServer(name, config)
    else:
        raise ValueError(f"Unsupported transport type: {transport}")


# 使用示例
async def example_usage():
    # 配置服务器列表，包含不同的传输协议
    servers_config = [
        {
            "name": "stdio-server",
            "transport": "stdio",
            "command": "npx",
            "args": ["claude-mcp-server"],
            "env": {"API_KEY": os.environ.get("API_KEY")}
        },
        {
            "name": "http-server",
            "transport": "streamable-http",
            "url": "http://localhost:3000/mcp",
            # "api_key": "your-api-key-here",  # 可选：如果服务器需要认证
            # "headers": {"Custom-Header": "value"},  # 可选：自定义headers
            # "timeout": 60,  # 可选：HTTP超时时间（秒）
            # "sse_read_timeout": 300,  # 可选：SSE读取超时时间（秒）
        },
        {
            "name": "sse-server", 
            "transport": "sse",
            "url": "http://localhost:8000/sse",
            # "api_key": "your-api-key-here",  # 可选：如果服务器需要认证
            # "headers": {"Custom-Header": "value"},  # 可选：自定义headers
            # "timeout": 5,  # 可选：HTTP连接超时时间（秒）
            # "sse_read_timeout": 300,  # 可选：SSE读取超时时间（秒）
        }
    ]

    # 创建并初始化所有服务器
    servers = []
    for config in servers_config:
        server = create_server(config["name"], config)
        try:
            await server.initialize()
            servers.append(server)
        except Exception as e:
            logging.error(f"Failed to initialize {config['name']}: {e}")
    
    # 列出所有服务器的工具
    all_tools = []
    for server in servers:
        try:
            tools = await server.list_tools()
            all_tools.extend(tools)
        except Exception as e:
            logging.error(f"Failed to list tools from {server.name}: {e}")
    
    # 清理所有服务器资源
    for server in servers:
        await server.cleanup()
        
    return all_tools


# 主程序入口点 - 如果需要运行示例
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(example_usage())