zhkzly: 请基于上述的库，为我讲解其各个文件夹的联系，其中主要的类，以及如何实现的功能，在解释的时候请给出代码示例，

GitHub Copilot: 好的，我来为您讲解这个 Python SDK 的结构、主要类和功能实现。

这个项目看起来是一个用于实现某种客户端-服务器通信协议（可能称为 MCP，Model Context Protocol）的 Python SDK。

**文件夹结构与联系：**

1.  **mcp**: 这是 SDK 的核心代码所在地。
    *   `client/`: 包含了实现 MCP 客户端逻辑的类和函数。客户端使用这些组件来连接服务器、发送请求和接收响应。
    *   `server/`: 包含了实现 MCP 服务器逻辑的类和函数。服务器使用这些组件来监听客户端连接、处理请求并发送响应。这里通常会定义如何暴露服务和工具。
    *   `shared/`: 包含客户端和服务器共用的代码，例如数据模型、序列化/反序列化逻辑、通用的网络处理工具等。
    *   `types.py`: 定义了整个 SDK 中使用的数据类型、枚举、以及可能的消息结构。这对于确保客户端和服务器之间的数据一致性非常重要。
    *   `cli/`: 可能包含用于与 SDK 交互或管理服务器/客户端的命令行界面工具。

2.  **examples**: 提供了如何使用此 SDK 的示例代码。
    *   `clients/`: 包含各种 MCP 客户端的示例实现。
    *   `servers/`: 包含各种 MCP 服务器的示例实现，展示了如何定义和暴露不同的服务。
    *   `fastmcp/`: 可能是一些快速上手或特定场景下的 MCP 应用示例。这些示例通常比较简单，适合初学者理解核心功能。

3.  **tests**: 包含了 SDK 的单元测试和集成测试。
    *   其内部结构通常会镜像 src 目录，针对每个模块和功能点进行测试。
    *   `issues/`: 存放针对特定报告的 bug 或问题的回归测试。

4.  **docs**: 存放项目的文档。
    *   `api.md`: 可能是 API 参考文档。
    *   `index.md`: 通常是文档的入口页面。

5.  **根目录文件**:
    *   pyproject.toml: 定义了项目的构建系统、依赖项等 (PEP 518)。
    *   mkdocs.yml: MkDocs 文档生成器的配置文件。
    *   README.md: 项目的介绍和基本使用说明。

**主要类和功能实现（基于推测和通用 SDK 设计模式）：**

为了更具体地说明，我们需要查看一些关键文件。我将首先查看 types.py 来了解基础数据结构，然后查看一个简单的示例，例如 simple_echo.py，来理解其基本工作流程。

 这个 Python 库是 Model Context Protocol (MCP) 的一个实现，它允许客户端（如 AI 助手）与服务器（如代码编辑器或具有工具的环境）进行通信。

**主要文件夹及其联系：**

*   **mcp**: 这是库的核心代码所在。
    *   types.py: 定义了 MCP 协议中使用的数据结构和类型。这些是基于 Pydantic V2 模型构建的，用于确保数据在客户端和服务器之间的传输是类型安全的和结构化的。例如，`Request`, `Notification`, `Result`, `ErrorData` 等基本 JSON-RPC 结构，以及特定于 MCP 功能的类型如 `InitializeRequestParams`, `Resource`, `Tool` 等。
    *   `client/`: 包含实现 MCP 客户端逻辑的代码。客户端负责向服务器发送请求（例如，请求资源列表、调用工具）并处理响应。
    *   `server/`: 包含实现 MCP 服务器逻辑的代码。服务器负责响应客户端的请求，例如提供资源、执行工具等。`fastmcp.py` (在 fastmcp 中可以看到其用法) 可能是一个简化创建 MCP 服务器的框架。
    *   `shared/`: 包含客户端和服务器都可能用到的共享代码或工具函数。

*   **examples**: 包含如何使用此库的示例代码。
    *   `clients/`: 包含 MCP 客户端的示例。
    *   `fastmcp/`: 展示了如何使用 `FastMCP` 框架快速创建 MCP 服务器。例如，simple_echo.py 展示了一个简单的回显工具。
    *   `servers/`: 包含各种 MCP 服务器的示例，演示了不同的功能，如认证、提示、资源管理等。

*   **tests**: 包含库的单元测试和集成测试。确保库的各个部分按预期工作。
    *   `client/`, `server/`, `shared/`: 分别对应 mcp 中相应模块的测试。
    *   `issues/`: 可能包含针对特定已报告问题或错误的测试用例。

**主要类及其功能：**

1.  **Pydantic 模型 (定义在 types.py)**:
    *   **`Request` / `JSONRPCRequest`**: 代表客户端向服务器发送的请求。它通常包含一个 `method` (字符串，指示要执行的操作) 和 `params` (操作所需的参数)。
        ```python
        # 示例 (概念性的，实际使用会通过客户端库)
        class MyToolParams(RequestParams):
            input_data: str

        class MyToolRequest(Request[MyToolParams, Literal["my_tool/execute"]]):
            method: Literal["my_tool/execute"]
            params: MyToolParams
        ```
    *   **`Notification` / `JSONRPCNotification`**: 代表不需要响应的单向消息，例如服务器通知客户端状态已更改。
    *   **`Result` / `JSONRPCResponse`**: 代表服务器对请求的成功响应。它包含 `id` (与请求 ID 对应) 和 `result` (操作的结果)。
    *   **`ErrorData` / `JSONRPCError`**: 代表服务器在处理请求时发生的错误。
    *   **`Resource`**: 代表服务器可以提供的资源，如文件内容。它包含 `uri`, `name`, `description`, `mimeType` 等属性。
        ```python
        # 示例 (来自 types.py)
        class Resource(BaseModel):
            uri: Annotated[AnyUrl, UrlConstraints(host_required=False)]
            name: str
            description: str | None = None
            mimeType: str | None = None
            # ... 其他字段
        ```
    *   **`Tool` (在 types.py 中可能定义为 `Tool` 或类似的结构，或者通过服务器端装饰器间接定义)**: 代表服务器可以执行的操作或功能。通常包含名称、描述和输入/输出参数的模式。

2.  **服务器实现 (例如 `mcp.server.fastmcp.FastMCP` 或其他基类)**:
    *   这些类提供了构建 MCP 服务器的框架。它们处理传入的 JSON-RPC 消息，根据 `method` 将请求路由到相应的处理函数（工具），并构造响应。
    *   **工具定义**: 通常通过装饰器 (如 `@mcp.tool()`) 来定义服务器提供的工具。
        ```python
        # 示例 (来自 examples/fastmcp/simple_echo.py)
        from mcp.server.fastmcp import FastMCP

        mcp = FastMCP("Echo Server") # 创建服务器实例

        @mcp.tool() # 将函数注册为一个 MCP 工具
        def echo(text: str) -> str:
            """Echo the input text"""
            return text
        ```
        在这个例子中，`FastMCP` 类负责处理底层的 MCP 通信。当你用 `@mcp.tool()` 装饰 `echo` 函数时，`FastMCP` 会知道有一个名为 "echo" (或者根据约定生成的名称) 的工具可用。当客户端发送一个调用 "echo" 工具的请求时，`FastMCP` 会执行这个 `echo` 函数并将结果返回给客户端。

3.  **客户端实现 (例如 `mcp.client.Client` 或类似的类)**:
    *   这些类提供了与 MCP 服务器交互的方法。它们允许你连接到服务器，发送请求（如调用工具、列出资源）并接收响应或通知。

**如何实现功能：**

1.  **协议定义**: types.py 使用 Pydantic 模型定义了通信双方（客户端和服务器）都理解的数据结构。这确保了消息的格式和内容是一致的。
2.  **服务器端**:
    *   开发者使用像 `FastMCP` 这样的服务器框架。
    *   通过装饰器（如 `@mcp.tool()`) 或其他注册机制，将 Python 函数暴露为 MCP 工具。这些函数接收特定的输入参数 (由其类型注解和 MCP 类型定义)，并返回结果。
    *   服务器监听来自客户端的连接和请求。
    *   当收到请求时，服务器解析请求，找到对应的工具函数，使用请求中的参数调用该函数。
    *   函数执行完毕后，服务器将返回值包装成 MCP `Result` (或错误时的 `ErrorData`) 并发送回客户端。
3.  **客户端**:
    *   客户端库提供方法来连接到 MCP 服务器。
    *   客户端可以发送 `initialize` 请求来协商协议版本和能力。
    *   客户端可以发送请求来调用服务器上定义的工具，例如：`client.call_tool("echo", {"text": "Hello"})`。
    *   客户端库负责将这个调用转换为一个 JSON-RPC `Request` 对象，发送给服务器，并等待 `Response`。
    *   收到响应后，客户端库会解析它，并将结果（或错误）返回给调用者。

**代码示例 (基于 simple_echo.py)**

**服务器端 (simple_echo.py)**:

```python
from mcp.server.fastmcp import FastMCP

# 1. 创建 FastMCP 服务器实例，并给它一个名字
mcp = FastMCP("Echo Server")

# 2. 使用 @mcp.tool() 装饰器定义一个工具
#    - 函数名 'echo' 通常会成为工具的名称。
#    - 类型注解 (text: str) -> str 用于自动生成工具的输入/输出模式，
#      并进行数据验证。
@mcp.tool()
def echo(text: str) -> str:
    """Echo the input text""" # 文档字符串通常用作工具的描述
    return text

# (当这个脚本运行时，FastMCP 会启动一个服务器，监听请求)
```

**客户端 (概念性示例，实际代码会使用客户端库的方法)**:

```python
# 假设有一个 mcp_client 库
# from mcp_client import Client # 伪代码

# 1. 创建客户端并连接到服务器 (URL 和端口取决于服务器如何运行)
# client = Client("ws://localhost:8080") # 伪代码

# 2. 初始化连接 (通常是第一步)
# init_response = client.initialize(...) # 伪代码

# 3. 调用服务器上的 'echo' 工具
# try:
#     response = client.call_tool("echo", {"text": "Hello MCP!"}) # 伪代码
#     # 'response' 会是一个包含 'result' 字段的对象
#     echoed_text = response.result
#     print(f"Server echoed: {echoed_text}") # 输出: Server echoed: Hello MCP!
# except MCPError as e: # 伪代码
#     print(f"Error calling tool: {e}")

```

这个库通过清晰地分离协议定义 (types.py)、服务器逻辑 (`server/`) 和客户端逻辑 (`client/`)，并利用 Pydantic 进行数据验证和序列化，从而实现了一个健壮的 MCP 通信框架。示例代码 (examples) 则展示了如何实际使用这些组件来构建 MCP 应用程序。

zhkzly: 请基于上述的库，为我讲解其各个文件夹的联系，其中主要的类，以及如何实现的功能，在解释的时候请给出代码示例，

GitHub Copilot: 我将为您详细讲解这个 Model Context Protocol (MCP) Python SDK 的结构、主要类和功能实现。让我们深入了解各个部分之间的联系并提供代码示例。

## 项目结构及各部分联系

### 1. 核心源代码 (mcp)

这是库的核心实现，包含了协议定义、客户端和服务器实现：

* **types.py**: 定义了 MCP 协议的数据类型和模型，使用 Pydantic v2
* **`client/`**: 提供连接和与 MCP 服务器交互的客户端实现
* **`server/`**: 提供创建 MCP 服务器的框架和工具
* **`shared/`**: 包含客户端和服务器共享的功能，如网络处理、序列化等
* **`cli/`**: 命令行接口工具

### 2. 示例代码 (examples)

提供多种使用场景的实际例子：

* **`fastmcp/`**: 使用 FastMCP 框架创建简单服务器的示例
* **`clients/`**: 客户端实现示例
* **`servers/`**: 不同类型的服务器实现示例

### 3. 测试代码 (tests)

确保库的各个部分正常工作：

* **`client/`**, **`server/`**, **`shared/`**: 对应各模块的测试
* **`issues/`**: 针对特定 bug 或问题的回归测试

### 4. 文档 (docs)

* **`api.md`**: API 参考文档
* **`index.md`**: 文档入口

## 主要类及其功能

让我们首先查看另一个更复杂的示例，以便更好地理解库的功能： 现在让我们来看看客户端实现： 让我们看看服务器端实现的详细示例： 让我们再查看一下客户端代码： 现在让我们查看几个关键文件，以便更全面地理解库的结构： ## MCP (Model Context Protocol) Python SDK 详解

基于查看到的文件和代码，我将为您详细讲解 MCP Python SDK 的结构、主要类和功能实现。

### 一、项目结构及关联

#### 1. 核心源代码 (mcp)

* **types.py**: 定义所有 MCP 协议数据结构，基于 Pydantic V2 构建
* **`client/`**: 客户端实现，用于连接 MCP 服务器
* **`server/`**: 服务器实现，特别是 FastMCP 框架
* **`shared/`**: 客户端和服务器共用的代码（序列化、传输等）
* **`cli/`**: 命令行工具

#### 2. 示例代码 (examples)

* **`fastmcp/`**: 演示如何使用 FastMCP 框架创建服务器
* **`clients/`**: 客户端实现示例，如 simple-chatbot、simple-auth-client 等
* **`servers/`**: 服务器实现示例，展示不同类型的服务器（认证、资源等）

#### 3. 测试代码 (tests)

* **`client/`**, **`server/`**, **`shared/`**: 各模块测试
* **`issues/`**: 针对特定 bug 的回归测试

### 二、主要类及其功能

#### 1. types.py - 基础数据结构

这个文件定义了 MCP 协议使用的所有数据类型。主要包括：

1. **请求与响应结构**:
   * `Request`/`JSONRPCRequest`: 客户端向服务器发送的请求
   * `Result`/`JSONRPCResponse`: 服务器返回的结果
   * `Notification`/`JSONRPCNotification`: 不需要响应的通知
   * `ErrorData`/`JSONRPCError`: 错误信息

2. **协议特定类型**:
   * `Resource`: 服务器提供的资源
   * `Tool`: 服务器提供的工具
   * `Prompt`: 服务器提供的提示模板

```python
# 核心请求结构 (来自 types.py)
class Request(BaseModel, Generic[RequestParamsT, MethodT]):
    """Base class for JSON-RPC requests."""
    method: MethodT
    params: RequestParamsT
    model_config = ConfigDict(extra="allow")

# 响应结构
class Result(BaseModel):
    """Base class for JSON-RPC results."""
    model_config = ConfigDict(extra="allow")
    meta: dict[str, Any] | None = Field(alias="_meta", default=None)
```

#### 2. `FastMCP` - 服务器框架

这是构建 MCP 服务器的核心类，提供了简洁的接口来定义工具、资源和提示模板。

```python
from mcp.server.fastmcp import FastMCP

# 创建服务器实例
mcp = FastMCP("My Server", instructions="这是一个示例服务器")

# 定义工具
@mcp.tool(description="回显输入文本")
def echo(text: str) -> str:
    """回显输入的文本"""
    return text

# 定义资源
@mcp.resource("file://example.txt")
def get_example_text():
    """提供示例文本内容"""
    return "这是一个示例文本资源"

# 定义参数化资源
@mcp.resource("file://user/{user_id}/profile")
def get_user_profile(user_id: str):
    """获取用户资料"""
    return f"用户 {user_id} 的资料"

# 定义提示模板
@mcp.prompt(description="一个简单的提示模板")
def simple_prompt(topic: str) -> str:
    return f"请详细介绍 {topic}"

# 运行服务器
if __name__ == "__main__":
    mcp.run(transport="streamable-http")
```

`FastMCP` 类提供的关键功能:

* **工具注册**: `@mcp.tool()` 装饰器将 Python 函数注册为 MCP 工具
* **资源管理**: `@mcp.resource()` 装饰器将函数转换为可访问的资源
* **提示管理**: `@mcp.prompt()` 装饰器定义可复用的提示模板
* **传输支持**: 支持多种传输协议 (stdio, SSE, Streamable HTTP)

#### 3. `ClientSession` - 客户端会话

这是客户端与服务器交互的主要类，处理初始化、请求发送和响应处理：

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# 创建服务器参数
server_params = StdioServerParameters(
    command="python",  # 可执行文件
    args=["server_script.py"],  # 命令行参数
)

async def run():
    # 连接到服务器
    async with stdio_client(server_params) as (read_stream, write_stream):
        # 创建会话
        async with ClientSession(read_stream, write_stream) as session:
            # 初始化连接
            result = await session.initialize()
            
            # 列出可用工具
            tools = await session.list_tools()
            print(f"可用工具: {[tool.name for tool in tools.tools]}")
            
            # 调用工具
            echo_result = await session.call_tool("echo", {"text": "你好，世界!"})
            print(f"回显结果: {echo_result.content[0].text}")
            
            # 读取资源
            resource = await session.read_resource("file://example.txt")
            print(f"资源内容: {resource.contents[0].text}")

# 运行客户端
import asyncio
asyncio.run(run())
```

#### 4. `Context` - 工具上下文

在 FastMCP 中，工具可以接收上下文对象，允许访问会话、发送日志和进度通知：

```python
from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP("Progress Server")

@mcp.tool(description="示范进度报告的工具")
async def process_with_progress(text: str, ctx: Context, steps: int = 5) -> str:
    """处理文本并显示进度"""
    # 记录日志
    await ctx.info(f"开始处理 '{text}'")
    
    # 发送进度通知
    for i in range(steps):
        # 计算进度百分比
        progress = (i + 1) / steps
        
        # 发送进度更新
        await ctx.report_progress(
            progress=progress,
            total=1.0,
            message=f"步骤 {i+1}/{steps} 完成"
        )
        
        # 添加调试日志
        await ctx.debug(f"完成步骤 {i+1}")
        
        # 模拟处理时间
        await asyncio.sleep(0.5)
    
    # 记录完成日志
    await ctx.info("处理完成")
    
    return f"已处理文本: {text} (共 {steps} 步)"
```

#### 5. OAuth 认证支持

MCP SDK 提供了完整的 OAuth 认证支持：

```python
from mcp.client.auth import OAuthClientProvider, TokenStorage
from mcp.client.streamable_http import streamablehttp_client
from mcp.client.session import ClientSession
from mcp.shared.auth import OAuthClientMetadata

# 自定义令牌存储
class InMemoryTokenStorage(TokenStorage):
    """简单的内存令牌存储"""
    def __init__(self):
        self._tokens = None
    
    async def store_tokens(self, tokens):
        self._tokens = tokens
        
    async def get_tokens(self):
        return self._tokens

async def main():
    # 创建 OAuth 客户端提供程序
    oauth_auth = OAuthClientProvider(
        server_url="https://api.example.com",
        client_metadata=OAuthClientMetadata(
            client_name="My MCP Client",
            redirect_uris=["http://localhost:3000/callback"],
            grant_types=["authorization_code", "refresh_token"],
            response_types=["code"],
        ),
        storage=InMemoryTokenStorage(),
        # 处理授权重定向
        redirect_handler=lambda url: print(f"请访问: {url}"),
        # 处理回调
        callback_handler=lambda: get_authorization_code()
    )
    
    # 创建已认证的连接
    async with streamablehttp_client(
        "https://api.example.com/mcp",
        auth=oauth_auth
    ) as (read_stream, write_stream, _):
        # 创建会话
        async with ClientSession(read_stream, write_stream) as session:
            # 初始化会话
            await session.initialize()
            # 调用受保护的工具
            result = await session.call_tool("get_profile", {})
            print(f"结果: {result}")
```

### 三、实现功能的方式

#### 1. 工具实现

MCP 服务器工具是通过 Python 函数实现的，利用类型注解自动生成 JSON Schema 描述：

```python
from typing import Annotated, List
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("数据处理服务器")

# 使用 Pydantic 复杂模型
class UserProfile(BaseModel):
    name: str
    age: Annotated[int, Field(ge=0, le=120)]
    interests: List[str]

@mcp.tool(description="处理用户资料")
def process_profile(
    profile: UserProfile,
    detailed: bool = False
) -> dict:
    """处理用户资料数据"""
    result = {"name": profile.name}
    
    if detailed:
        result.update({
            "age": profile.age,
            "interests": profile.interests,
            "interest_count": len(profile.interests)
        })
    
    return result
```

当客户端调用此工具时，FastMCP 会：
1. 验证传入参数 (`profile` 和 `detailed`)
2. 验证 `profile` 是否符合 `UserProfile` 模型规范
3. 执行函数逻辑
4. 将返回值序列化为 JSON 并发送回客户端

#### 2. 资源实现

资源可以是文件、函数生成的内容或模板化内容：

```python
from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("文件服务器")

# 静态文件资源
@mcp.resource("file://configs/default.json", 
              mime_type="application/json")
def get_default_config():
    return Path("configs/default.json").read_text()

# 动态生成资源
@mcp.resource("data://current/stats")
def get_current_stats():
    # 动态生成统计数据
    return {"users": 1205, "active": 503, "timestamp": time.time()}

# 模板化资源 (URI 参数映射到函数参数)
@mcp.resource("user://{user_id}/details")
def get_user_details(user_id: str):
    # 根据 ID 获取用户详情
    user = database.get_user(user_id)
    return user.to_dict()
```

#### 3. 支持的传输协议

MCP SDK 支持三种主要的传输协议：

1. **stdio**: 使用标准输入/输出进行通信，适用于子进程通信
   ```python
   mcp.run(transport="stdio")
   ```

2. **SSE (Server-Sent Events)**: 基于 HTTP 的长连接，支持服务器向客户端推送事件
   ```python
   mcp.run(transport="sse")
   ```

3. **Streamable HTTP**: 新一代传输协议，支持双向通信和无状态操作
   ```python
   # 有状态模式 (保持会话)
   mcp.run(transport="streamable-http")
   
   # 无状态模式 (每个请求独立)
   mcp = FastMCP("StatelessServer", stateless_http=True)
   mcp.run(transport="streamable-http")
   ```

#### 4. 客户端-服务器通信流程

1. **初始化**:
   - 客户端发送 `initialize` 请求，包含支持的协议版本和功能
   - 服务器响应其支持的功能和版本信息
   - 客户端发送 `initialized` 通知

2. **功能发现**:
   - 客户端调用 `list_tools()` 获取可用工具
   - 客户端调用 `list_resources()` 获取可用资源
   - 客户端调用 `list_prompts()` 获取可用提示模板

3. **工具调用**:
   - 客户端发送 `tools/call` 请求
   - 服务器执行相应函数
   - 服务器返回结果

4. **资源请求**:
   - 客户端发送 `resources/read` 请求
   - 服务器读取或生成资源内容
   - 服务器返回内容

5. **获取提示**:
   - 客户端发送 `prompts/get` 请求
   - 服务器用参数填充提示模板
   - 服务器返回完整提示

### 四、完整的实际示例

#### 1. 创建一个完整的服务器

```python
from typing import List, Optional
from pathlib import Path
from mcp.server.fastmcp import FastMCP, Context

# 创建服务器
mcp = FastMCP(
    name="文档处理服务",
    instructions="这个服务提供文档处理和搜索功能"
)

# 工具：文本分析
@mcp.tool(description="分析文本并返回统计信息")
def analyze_text(text: str) -> dict:
    """分析文本并返回单词数量、行数等统计信息"""
    lines = text.split("\n")
    words = text.split()
    
    return {
        "lines": len(lines),
        "words": len(words),
        "characters": len(text),
        "avg_word_length": sum(len(w) for w in words) / max(len(words), 1)
    }

# 工具：带进度的长时间运行任务
@mcp.tool(description="模拟需要长时间执行的任务")
async def long_running_task(
    iterations: int,
    ctx: Context,
    delay: float = 0.2
) -> List[dict]:
    """执行一个模拟的长时间任务，显示进度"""
    results = []
    
    # 记录任务开始
    await ctx.info(f"开始处理 {iterations} 次迭代")
    
    for i in range(iterations):
        # 计算和报告进度
        progress = (i + 1) / iterations
        await ctx.report_progress(
            progress=progress,
            total=1.0,
            message=f"完成 {i+1}/{iterations} 次迭代" 
        )
        
        # 执行工作并添加结果
        result = {"iteration": i, "value": i * i}
        results.append(result)
        
        # 记录调试信息
        await ctx.debug(f"迭代 {i} 结果: {result}")
        
        # 模拟处理时间
        await asyncio.sleep(delay)
    
    await ctx.info("任务完成")
    return results

# 资源：文件列表
@mcp.resource("dir://docs")
def list_docs():
    """列出文档目录中的所有文件"""
    docs_dir = Path("docs")
    files = [f.name for f in docs_dir.glob("*.md")]
    return files

# 参数化资源：获取特定文档
@mcp.resource("file://docs/{filename}")
def get_document(filename: str) -> str:
    """获取特定文档的内容"""
    try:
        file_path = Path("docs") / filename
        if not file_path.is_file() or not filename.endswith(".md"):
            return f"错误: 找不到文档 '{filename}'"
        return file_path.read_text()
    except Exception as e:
        return f"读取文档时出错: {str(e)}"

# 提示模板
@mcp.prompt(description="文档摘要提示")
def summarize_prompt(text: str, max_words: int = 100) -> str:
    """为文档摘要生成提示"""
    return f"""请对以下文本进行摘要，摘要不超过 {max_words} 个词:

{text}

摘要:"""

# 运行服务器 (支持 stdio, sse 或 streamable-http)
if __name__ == "__main__":
    mcp.run(transport="streamable-http")
```

#### 2. 创建一个完整的客户端

```python
import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def main():
    print("连接到 MCP 服务器...")
    
    # 连接到服务器
    async with streamablehttp_client("http://localhost:8000/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            # 初始化连接
            result = await session.initialize()
            print(f"已连接到: {result.serverInfo.name}")
            print(f"协议版本: {result.protocolVersion}")
            if result.instructions:
                print(f"服务器说明: {result.instructions}")
            
            # 获取可用工具
            tools = await session.list_tools()
            print("\n可用工具:")
            for i, tool in enumerate(tools.tools, 1):
                print(f"  {i}. {tool.name}: {tool.description}")
            
            # 获取可用资源
            resources = await session.list_resources()
            print("\n可用资源:")
            for i, resource in enumerate(resources.resources, 1):
                print(f"  {i}. {resource.name} ({resource.uri})")
            
            # 列出可用提示模板
            prompts = await session.list_prompts()
            print("\n可用提示模板:")
            for i, prompt in enumerate(prompts.prompts, 1):
                print(f"  {i}. {prompt.name}: {prompt.description}")
            
            # 调用文本分析工具
            sample_text = "这是一个示例文本。\n它有两行。"
            print(f"\n分析文本: '{sample_text}'")
            analysis = await session.call_tool("analyze_text", {"text": sample_text})
            print("分析结果:")
            print(f"  行数: {analysis.content[0].text['lines']}")
            print(f"  词数: {analysis.content[0].text['words']}")
            print(f"  字符数: {analysis.content[0].text['characters']}")
            
            # 读取资源列表
            print("\n获取文档列表...")
            docs = await session.read_resource("dir://docs")
            file_list = docs.contents[0].text
            print(f"可用文档: {file_list}")
            
            # 如果有文档，读取第一个
            if file_list:
                first_doc = file_list[0]
                print(f"\n读取文档: {first_doc}")
                doc_content = await session.read_resource(f"file://docs/{first_doc}")
                content = doc_content.contents[0].text
                print(f"文档内容: {content[:100]}...")  # 只显示前100个字符
                
                # 获取摘要提示
                print("\n获取摘要提示...")
                prompt = await session.get_prompt("summarize_prompt", {
                    "text": content,
                    "max_words": 50
                })
                print(f"提示内容: {prompt.prompt}")
            
            # 执行长时间运行的任务（带进度更新）
            print("\n执行长时间任务...")
            task_result = await session.call_tool("long_running_task", {
                "iterations": 5,
                "delay": 0.5
            })
            print("任务结果:")
            for item in task_result.content[0].text:
                print(f"  迭代 {item['iteration']}: {item['value']}")

if __name__ == "__main__":
    asyncio.run(main())
```

通过这些代码示例，您可以看到 MCP SDK 允许开发者创建功能丰富的服务器和客户端，支持类型安全的工具调用、资源访问、提示模板和进度通知等功能。它为客户端和服务器之间的通信提供了一个结构化、类型安全的框架。

zhkzly: import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def main():
    print("连接到 MCP 服务器...")
    
    # 连接到服务器
    async with streamablehttp_client("http://localhost:8000/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            # 初始化连接
            result = await session.initialize()
            print(f"已连接到: {result.serverInfo.name}")
            print(f"协议版本: {result.protocolVersion}")
            if result.instructions:
                print(f"服务器说明: {result.instructions}")
            
            # 获取可用工具
            tools = await session.list_tools()
            print("\n可用工具:")
            for i, tool in enumerate(tools.tools, 1):
                print(f"  {i}. {tool.name}: {tool.description}")
            
            # 获取可用资源
            resources = await session.list_resources()
            print("\n可用资源:")
            for i, resource in enumerate(resources.resources, 1):
                print(f"  {i}. {resource.name} ({resource.uri})")
            
            # 列出可用提示模板
            prompts = await session.list_prompts()
            print("\n可用提示模板:")
            for i, prompt in enumerate(prompts.prompts, 1):
                print(f"  {i}. {prompt.name}: {prompt.description}")
            
            # 调用文本分析工具
            sample_text = "这是一个示例文本。\n它有两行。"
            print(f"\n分析文本: '{sample_text}'")
            analysis = await session.call_tool("analyze_text", {"text": sample_text})
            print("分析结果:")
            print(f"  行数: {analysis.content[0].text['lines']}")
            print(f"  词数: {analysis.content[0].text['words']}")
            print(f"  字符数: {analysis.content[0].text['characters']}")
            
            # 读取资源列表
            print("\n获取文档列表...")
            docs = await session.read_resource("dir://docs")
            file_list = docs.contents[0].text
            print(f"可用文档: {file_list}")
            
            # 如果有文档，读取第一个
            if file_list:
                first_doc = file_list[0]
                print(f"\n读取文档: {first_doc}")
                doc_content = await session.read_resource(f"file://docs/{first_doc}")
                content = doc_content.contents[0].text
                print(f"文档内容: {content[:100]}...")  # 只显示前100个字符
                
                # 获取摘要提示
                print("\n获取摘要提示...")
                prompt = await session.get_prompt("summarize_prompt", {
                    "text": content,
                    "max_words": 50
                })
                print(f"提示内容: {prompt.prompt}")
            
            # 执行长时间运行的任务（带进度更新）
            print("\n执行长时间任务...")
            task_result = await session.call_tool("long_running_task", {
                "iterations": 5,
                "delay": 0.5
            })
            print("任务结果:")
            for item in task_result.content[0].text:
                print(f"  迭代 {item['iteration']}: {item['value']}")

if __name__ == "__main__":
    asyncio.run(main())

    其中所需要的所有的 关键性的函数的实现讲解，请主要关注客户端，并且需要给出代码解释，继承关系，调用逻辑，输入输出，关键函数

GitHub Copilot: # MCP Python SDK 客户端部分解析

您提供的代码是使用 MCP (Model Context Protocol) SDK 创建的一个客户端应用程序。我将详细讲解其中关键函数的实现、继承关系、调用逻辑和输入输出。

## 核心类及继承关系

在 MCP 客户端中，有几个关键类：

1. **ClientSession**: 这是客户端的主要类，提供与服务器交互的方法
2. **BaseSession**: `ClientSession` 继承自这个基类，提供通用会话功能
3. **streamablehttp_client**: 提供 Streamable HTTP 传输连接的上下文管理器
4. **TokenStorage**: OAuth 认证的令牌存储接口，用于存储访问令牌
5. **OAuthClientProvider**: 提供 OAuth 认证功能

继承关系图：
```
BaseSession
    └── ClientSession
```

## 关键函数详解

### 1. `streamablehttp_client` - 创建连接

```python
async with streamablehttp_client("http://localhost:8000/mcp") as (read, write, _):
    # ...
```

**功能**: 创建与 MCP 服务器的 Streamable HTTP 连接。

**输入**:
- URL: 服务器地址 (例如 "http://localhost:8000/mcp")
- 可选参数: headers, timeout, auth, terminate_on_close 等

**输出**: 返回一个三元组 (read_stream, write_stream, get_session_id)
- read_stream: 用于接收服务器消息的流
- write_stream: 用于发送消息到服务器的流
- get_session_id: 用于获取会话 ID 的函数

**实现原理**:
1. 初始化 HTTP 客户端连接
2. 创建内存流来处理消息交换
3. 在后台启动读写任务
4. 返回读写流供 ClientSession 使用

### 2. `ClientSession.__init__` - 初始化会话

```python
async with ClientSession(read, write) as session:
    # ...
```

**功能**: 创建和初始化 MCP 客户端会话。

**输入**:
- read_stream: 从服务器读取消息的流
- write_stream: 向服务器写入消息的流
- 可选参数: sampling_callback, list_roots_callback 等

**实现原理** (从 session.py):
```python
def __init__(
    self,
    read_stream: MemoryObjectReceiveStream[SessionMessage | Exception],
    write_stream: MemoryObjectSendStream[SessionMessage],
    read_timeout_seconds: timedelta | None = None,
    sampling_callback: SamplingFnT | None = None,
    list_roots_callback: ListRootsFnT | None = None,
    logging_callback: LoggingFnT | None = None,
    message_handler: MessageHandlerFnT | None = None,
    client_info: types.Implementation | None = None,
) -> None:
    super().__init__(
        read_stream,
        write_stream,
        types.ServerRequest,
        types.ServerNotification,
        read_timeout_seconds=read_timeout_seconds,
    )
    self._client_info = client_info or DEFAULT_CLIENT_INFO
    self._sampling_callback = sampling_callback or _default_sampling_callback
    self._list_roots_callback = list_roots_callback or _default_list_roots_callback
    self._logging_callback = logging_callback or _default_logging_callback
    self._message_handler = message_handler or _default_message_handler
```

### 3. `session.initialize()` - 初始化连接

```python
result = await session.initialize()
```

**功能**: 与服务器建立初始连接并协商协议版本和功能。

**输出**: `InitializeResult` 对象，包含:
- serverInfo: 服务器信息，包含 name 和 version
- protocolVersion: 协议版本
- capabilities: 服务器能力
- instructions: 可选的服务器使用说明

**实现原理**:
```python
async def initialize(self) -> types.InitializeResult:
    sampling = types.SamplingCapability()
    roots = types.RootsCapability(listChanged=True)

    result = await self.send_request(
        types.ClientRequest(
            types.InitializeRequest(
                method="initialize",
                params=types.InitializeRequestParams(
                    protocolVersion=types.LATEST_PROTOCOL_VERSION,
                    capabilities=types.ClientCapabilities(
                        sampling=sampling,
                        experimental=None,
                        roots=roots,
                    ),
                    clientInfo=self._client_info,
                ),
            )
        ),
        types.InitializeResult,
    )

    if result.protocolVersion not in SUPPORTED_PROTOCOL_VERSIONS:
        raise RuntimeError(
            f"Unsupported protocol version: {result.protocolVersion}"
        )

    await self.send_notification(
        types.ClientNotification(
            types.InitializedNotification(method="notifications/initialized")
        )
    )

    return result
```

### 4. `session.list_tools()` - 获取可用工具

```python
tools = await session.list_tools()
```

**功能**: 获取服务器提供的所有工具列表。

**输出**: `ListToolsResult` 对象，包含:
- tools: 工具列表，每个工具包含 name, description, inputSchema 等

**实现原理**:
```python
async def list_tools(self) -> types.ListToolsResult:
    return await self.send_request(
        types.ClientRequest(
            types.ListToolsRequest(method="tools/list")
        ),
        types.ListToolsResult,
    )
```

### 5. `session.list_resources()` - 获取可用资源

```python
resources = await session.list_resources()
```

**功能**: 获取服务器提供的所有资源列表。

**输出**: `ListResourcesResult` 对象，包含:
- resources: 资源列表，每个资源包含 uri, name, description, mimeType 等

**实现原理**:
```python
async def list_resources(self) -> types.ListResourcesResult:
    return await self.send_request(
        types.ClientRequest(
            types.ListResourcesRequest(method="resources/list")
        ),
        types.ListResourcesResult,
    )
```

### 6. `session.list_prompts()` - 获取可用提示模板

```python
prompts = await session.list_prompts()
```

**功能**: 获取服务器提供的所有提示模板列表。

**输出**: `ListPromptsResult` 对象，包含:
- prompts: 提示模板列表，每个模板包含 name, description, inputSchema 等

**实现原理**:
```python
async def list_prompts(self) -> types.ListPromptsResult:
    return await self.send_request(
        types.ClientRequest(
            types.ListPromptsRequest(method="prompts/list")
        ),
        types.ListPromptsResult,
    )
```

### 7. `session.call_tool()` - 调用工具

```python
analysis = await session.call_tool("analyze_text", {"text": sample_text})
```

**功能**: 调用服务器上的指定工具。

**输入**:
- name: 工具名称
- arguments: 工具参数字典

**输出**: `CallToolResult` 对象，包含:
- content: 包含工具执行结果的内容列表 (TextContent, ImageContent 等)

**实现原理**:
```python
async def call_tool(
    self,
    name: str,
    arguments: dict[str, Any] | None = None,
) -> types.CallToolResult:
    return await self.send_request(
        types.ClientRequest(
            types.CallToolRequest(
                method="tools/call",
                params=types.CallToolRequestParams(
                    name=name, arguments=arguments or {}
                ),
            )
        ),
        types.CallToolResult,
    )
```

### 8. `session.read_resource()` - 读取资源

```python
docs = await session.read_resource("dir://docs")
```

**功能**: 读取服务器上的指定资源。

**输入**:
- uri: 资源 URI

**输出**: `ReadResourceResult` 对象，包含:
- contents: 资源内容列表 (TextResourceContents, BlobResourceContents 等)

**实现原理**:
```python
async def read_resource(self, uri: AnyUrl) -> types.ReadResourceResult:
    return await self.send_request(
        types.ClientRequest(
            types.ReadResourceRequest(
                method="resources/read",
                params=types.ReadResourceRequestParams(uri=uri),
            )
        ),
        types.ReadResourceResult,
    )
```

### 9. `session.get_prompt()` - 获取提示模板

```python
prompt = await session.get_prompt("summarize_prompt", {
    "text": content,
    "max_words": 50
})
```

**功能**: 获取并应用特定的提示模板。

**输入**:
- name: 提示模板名称
- arguments: 提示模板参数字典

**输出**: `GetPromptResult` 对象，包含:
- prompt: 生成的提示内容

**实现原理**:
```python
async def get_prompt(
    self, name: str, arguments: dict[str, Any] | None = None
) -> types.GetPromptResult:
    return await self.send_request(
        types.ClientRequest(
            types.GetPromptRequest(
                method="prompts/get",
                params=types.GetPromptRequestParams(
                    name=name, arguments=arguments or {}
                ),
            )
        ),
        types.GetPromptResult,
    )
```

## 核心调用逻辑

MCP 客户端的通信流程遵循以下模式：

1. **建立连接**：使用 `streamablehttp_client` 或其他传输客户端建立连接
2. **创建会话**：使用流创建 `ClientSession` 对象
3. **初始化协议**：
   - 客户端发送 `initialize` 请求，提供客户端信息和支持的功能
   - 服务器响应其功能和信息
   - 客户端发送 `initialized` 通知
4. **发现服务器功能**：调用 `list_tools()`, `list_resources()` 和 `list_prompts()`
5. **调用特定功能**：
   - 调用工具：`call_tool()`
   - 读取资源：`read_resource()`
   - 获取提示：`get_prompt()`

所有这些操作都依赖于底层的请求-响应机制，由 `BaseSession` 中的 `send_request()` 方法提供：

```python
async def send_request[RequestParamsT, RequestMethodT, ResponseT](
    self,
    request: RequestRootT[RequestParamsT, RequestMethodT],
    response_type: type[ResponseT],
) -> ResponseT:
    # 生成请求 ID
    request_id = self._next_request_id()
    
    # 创建完整的 JSON-RPC 请求
    jsonrpc_request = JSONRPCRequest(
        jsonrpc="2.0",
        id=request_id,
        method=request.root.method,
        params=request.root.params.model_dump(by_alias=True, mode="json", exclude_none=True)
        if hasattr(request.root.params, "model_dump")
        else request.root.params,
    )
    
    # 发送请求并等待响应
    response = await self._session_send_and_receive_response(
        jsonrpc_request, request_id
    )
    
    # 验证并返回结果
    try:
        return response_type.model_validate(response.result)
    except Exception as e:
        raise McpError(f"Failed to validate response: {e}") from e
```

## 结论

MCP Python SDK 的客户端部分提供了一个优雅且类型安全的方式来与 MCP 服务器交互。它通过 JSON-RPC 协议处理通信，并使用 Pydantic 模型确保类型安全。核心类 `ClientSession` 提供了丰富的方法来发现和使用服务器功能，如工具、资源和提示模板。

客户端的设计理念是基于异步编程模型，使用 `async/await` 语法和上下文管理器，这使得代码更加简洁和可读，同时也提供了更好的资源管理。不同的传输方式（如 stdio、SSE 和 Streamable HTTP）共享相同的客户端接口，这使得切换传输方式变得简单明了。

zhkzly: async def send_request[RequestParamsT, RequestMethodT, ResponseT](
    self,
    request: RequestRootT[RequestParamsT, RequestMethodT],
    response_type: type[ResponseT],
) -> ResponseT:

上面这几个泛型是如何定义的？？

GitHub Copilot: 您询问的是 `send_request` 方法中使用的泛型参数的定义方式。这些泛型参数是 Python 的类型注解系统的一部分，用于实现泛型编程。在 MCP Python SDK 中，这些泛型参数的定义和使用方式相当复杂，我来详细解释一下。

在 MCP 的 `BaseSession` 类中，这些泛型参数是这样定义的：

```python
class BaseSession[
    RequestRootT,  # 客户端请求的根类型
    NotificationRootT,  # 客户端通知的根类型
    ResultRootT,  # 客户端结果的根类型
    ServerRequestRootT,  # 服务器请求的根类型
    ServerNotificationRootT,  # 服务器通知的根类型
]:
    # 类实现...
```

这是 Python 3.12 引入的新语法，用于直接在类定义中声明类型参数。在较早的版本中，通常使用 `Generic` 来实现类似功能：

```python
class BaseSession(Generic[RequestRootT, NotificationRootT, ResultRootT, ServerRequestRootT, ServerNotificationRootT]):
    # 类实现...
```

然后，在 `send_request` 方法中使用了方法级的泛型参数：

```python
async def send_request[RequestParamsT, RequestMethodT, ResponseT](
    self,
    request: RequestRootT[RequestParamsT, RequestMethodT],
    response_type: type[ResponseT],
) -> ResponseT:
    # 方法实现...
```

这些泛型参数的含义如下：

1. **RequestParamsT**: 表示请求参数的类型，例如 `CallToolRequestParams`、`ReadResourceRequestParams` 等。
2. **RequestMethodT**: 表示请求方法的类型，通常是 `Literal` 类型，如 `Literal["tools/call"]`。
3. **ResponseT**: 表示预期的响应类型，例如 `CallToolResult`、`ReadResourceResult` 等。
4. **RequestRootT**: 是 `BaseSession` 类泛型参数，表示客户端请求的根类型，如 `ClientRequest`。

这些泛型参数在源代码中的定义可能是这样的：

```python
# 在 session.py 中
from typing import Any, Generic, TypeVar

RequestParamsT = TypeVar("RequestParamsT", bound=Any)
RequestMethodT = TypeVar("RequestMethodT", bound=str)
ResponseT = TypeVar("ResponseT", bound=Any)

RequestRootT = TypeVar("RequestRootT", bound="Request[Any, Any]")
NotificationRootT = TypeVar("NotificationRootT", bound="Notification[Any, Any]")
ResultRootT = TypeVar("ResultRootT", bound=Any)
ServerRequestRootT = TypeVar("ServerRequestRootT", bound=Any)
ServerNotificationRootT = TypeVar("ServerNotificationRootT", bound=Any)
```

`send_request` 方法使用这些泛型参数来确保类型安全：

1. 参数 `request` 必须是 `RequestRootT` 类型，并且包含 `RequestParamsT` 和 `RequestMethodT` 类型的参数。
2. 参数 `response_type` 必须是 `type[ResponseT]`，即 `ResponseT` 的类型对象。
3. 方法返回 `ResponseT` 类型的结果。

例如，当调用 `call_tool` 时，实际上会调用 `send_request`：

```python
async def call_tool(
    self,
    name: str,
    arguments: dict[str, Any] | None = None,
) -> types.CallToolResult:
    return await self.send_request(
        types.ClientRequest(
            types.CallToolRequest(
                method="tools/call",  # RequestMethodT = Literal["tools/call"]
                params=types.CallToolRequestParams(  # RequestParamsT = CallToolRequestParams
                    name=name, arguments=arguments or {}
                ),
            )
        ),
        types.CallToolResult,  # ResponseT = CallToolResult
    )
```

这种复杂的泛型系统确保了在编译时就能捕获类型错误，增强了代码的类型安全性和可维护性。

需要注意的是，方法级泛型 (如 `async def send_request[...]`) 是 Python 3.12 的新特性。在较早的 Python 版本中，这些泛型可能是通过其他方式实现的，例如使用类级泛型或类型注解中的泛型函数。

zhkzly: 请在本项目中为我找到这些泛型的定义

GitHub Copilot: 我将为您在 MCP Python SDK 项目中查找这些泛型的定义。让我使用工具搜索相关文件和定义。 Summarized conversation historySummarizing conversation history...我会帮您查找这个项目中的泛型定义。让我先用语义搜索查找相关代码。 让我继续搜索与泛型定义相关的内容，特别是在shared/session.py文件中。 让我现在查看client/session.py来了解具体的ClientSession实现是如何使用这些泛型的： 现在我已经找到了你所关心的MCP Python SDK中的泛型定义，让我来为你详细解释一下这些泛型类型变量是如何使用的。

# MCP Python SDK 中的泛型类型系统

## 核心泛型定义

在session.py中找到了关键的泛型类型变量定义，这些是`send_request`方法和整个通信框架的基础：

```python
SendRequestT = TypeVar("SendRequestT", ClientRequest, ServerRequest)
SendResultT = TypeVar("SendResultT", ClientResult, ServerResult)
SendNotificationT = TypeVar("SendNotificationT", ClientNotification, ServerNotification)
ReceiveRequestT = TypeVar("ReceiveRequestT", ClientRequest, ServerRequest)
ReceiveResultT = TypeVar("ReceiveResultT", bound=BaseModel)
ReceiveNotificationT = TypeVar(
    "ReceiveNotificationT", ClientNotification, ServerNotification
)
```

## 泛型类型参数的作用

这些泛型类型变量在`BaseSession`类中使用，用于定义客户端和服务器之间通信的不同消息类型：

1. **SendRequestT** - 发送请求的类型，限定为`ClientRequest`或`ServerRequest`
2. **SendResultT** - 发送结果的类型，限定为`ClientResult`或`ServerResult`
3. **SendNotificationT** - 发送通知的类型，限定为`ClientNotification`或`ServerNotification`
4. **ReceiveRequestT** - 接收请求的类型，限定为`ClientRequest`或`ServerRequest`
5. **ReceiveResultT** - 接收结果的类型，必须是`BaseModel`的子类
6. **ReceiveNotificationT** - 接收通知的类型，限定为`ClientNotification`或`ServerNotification`

## BaseSession 的泛型实现

`BaseSession`类使用这些泛型类型来定义会话的基本功能：

```python
class BaseSession(
    Generic[
        SendRequestT,
        SendNotificationT,
        SendResultT,
        ReceiveRequestT,
        ReceiveNotificationT,
    ],
):
    # ...
```

这个基类负责在客户端与服务器之间发送和接收消息，使用这些泛型类型来确保类型安全。

## 客户端和服务器如何使用这些泛型

### 1. ClientSession 实现

`ClientSession`通过具体化泛型类型来定义客户端发送和接收的消息类型：

```python
class ClientSession(
    BaseSession[
        types.ClientRequest,
        types.ClientNotification,
        types.ClientResult,
        types.ServerRequest,
        types.ServerNotification,
    ]
):
    # ...
```

这里，`ClientSession`指定：
- 发送请求类型为`ClientRequest`
- 发送通知类型为`ClientNotification`
- 发送结果类型为`ClientResult`
- 接收请求类型为`ServerRequest`
- 接收通知类型为`ServerNotification`

### 2. ServerSession 实现

同样，`ServerSession`反过来定义了服务器端的消息类型：

```python
class ServerSession(
    BaseSession[
        types.ServerRequest,
        types.ServerNotification,
        types.ServerResult,
        types.ClientRequest,
        types.ClientNotification,
    ]
):
    # ...
```

服务器会话指定：
- 发送请求类型为`ServerRequest`
- 发送通知类型为`ServerNotification`
- 发送结果类型为`ServerResult`
- 接收请求类型为`ClientRequest`
- 接收通知类型为`ClientNotification`

## send_request 方法中的泛型使用

`send_request`方法是`BaseSession`类中最重要的方法之一，它使用了这些泛型类型：

```python
async def send_request(
    self,
    request: SendRequestT,
    result_type: type[ReceiveResultT],
    request_read_timeout_seconds: timedelta | None = None,
    metadata: MessageMetadata = None,
    progress_callback: ProgressFnT | None = None,
) -> ReceiveResultT:
    # ...
```

这个方法:
1. 接受一个`SendRequestT`类型的请求参数
2. 接受一个期望的返回类型`result_type: type[ReceiveResultT]`
3. 返回`ReceiveResultT`类型的结果

这种设计确保了类型安全性，让客户端和服务器能够以类型安全的方式进行通信，同时共享相同的底层实现。

## 实用案例

在实际使用中，当调用`send_request`方法时：

```python
# 在ClientSession中
result = await self.send_request(
    types.ClientRequest(
        types.InitializeRequest(
            method="initialize",
            params=types.InitializeRequestParams(...),
        )
    ),
    types.InitializeResult,
)
```

这里：
1. 请求类型是`ClientRequest`
2. 期望的返回类型是`InitializeResult`
3. 方法会返回`InitializeResult`类型的实例

## 整体架构关系

这个通用泛型系统非常巧妙地解决了客户端和服务器通信的类型安全问题：

1. `BaseSession`提供了通用的通信框架和实现
2. `ClientSession`和`ServerSession`分别为客户端和服务器具体化了这些泛型类型
3. 在运行时，消息会根据其类型被正确地发送和接收
4. 系统使用Python的类型提示和泛型系统来确保类型安全，防止类型错误

这种设计允许客户端和服务器共享相同的底层通信逻辑，同时保持各自特定的消息类型和行为。

总的来说，MCP SDK的泛型系统是一个精心设计的类型系统，确保了客户端和服务器之间通信的类型安全，同时允许它们共享大部分实现代码。

zhkzly: # MCP Python SDK 客户端部分解析

您提供的代码是使用 MCP (Model Context Protocol) SDK 创建的一个客户端应用程序。我将详细讲解其中关键函数的实现、继承关系、调用逻辑和输入输出。

## 核心类及继承关系

在 MCP 客户端中，有几个关键类：

1. **ClientSession**: 这是客户端的主要类，提供与服务器交互的方法
2. **BaseSession**: `ClientSession` 继承自这个基类，提供通用会话功能
3. **streamablehttp_client**: 提供 Streamable HTTP 传输连接的上下文管理器
4. **TokenStorage**: OAuth 认证的令牌存储接口，用于存储访问令牌
5. **OAuthClientProvider**: 提供 OAuth 认证功能

继承关系图：
```
BaseSession
    └── ClientSession
```

## 关键函数详解

### 1. `streamablehttp_client` - 创建连接

```python
async with streamablehttp_client("http://localhost:8000/mcp") as (read, write, _):
    # ...
```

**功能**: 创建与 MCP 服务器的 Streamable HTTP 连接。

**输入**:
- URL: 服务器地址 (例如 "http://localhost:8000/mcp")
- 可选参数: headers, timeout, auth, terminate_on_close 等

**输出**: 返回一个三元组 (read_stream, write_stream, get_session_id)
- read_stream: 用于接收服务器消息的流
- write_stream: 用于发送消息到服务器的流
- get_session_id: 用于获取会话 ID 的函数

为什么需要是一个三元组，一个接收stream，一个write stream??不能直接就一个吗？？这个http 应该不是进程通信吧？


GitHub Copilot: # MCP Python SDK中为什么使用两个独立的流进行通信

你提出了一个很好的问题：为什么MCP SDK使用两个独立的流(一个读取流和一个写入流)，而不是一个单一的双向连接。这是一个设计选择，有几个重要的原因：

## 为什么使用两个独立的流

### 1. 抽象传输层设计

MCP SDK被设计成支持多种不同的传输协议，包括:

- Streamable HTTP
- Server-Sent Events (SSE)
- WebSockets
- 标准输入/输出(stdio)进程间通信

每种传输协议的具体实现可能不同，但它们都需要满足相同的接口要求 - 能够读取和写入消息。通过分离读写流，SDK可以为不同传输机制提供统一的接口。

### 2. 并发通信的支持

使用独立的读写流允许客户端同时发送和接收消息，而不需要等待响应。这对于支持以下场景非常重要:

- 异步请求/响应
- 服务器推送通知
- 进度更新

例如，客户端可以发送一个请求并继续接收之前请求的进度通知，而不会阻塞。

### 3. 流控制和缓冲区管理

分离读写流允许为每个方向独立配置缓冲区大小和流控制策略，这对于高性能应用程序和处理大型消息特别重要。

### 4. 统一的抽象模式

这种设计使得SDK可以使用相同的抽象模式处理不同传输协议的特性，例如:

- stdio使用两个独立的流(stdin和stdout)
- HTTP长轮询需要单独的请求和响应通道
- SSE是单向的(只能从服务器到客户端)，需要配合另一个向服务器发送数据的机制

## Streamable HTTP的工作原理

对于你特别提到的Streamable HTTP传输，它确实不是典型的进程间通信，而是使用HTTP协议的扩展。在Streamable HTTP中:

1. 客户端发起一个HTTP请求到服务器
2. 连接保持打开状态，允许双向数据流
3. 客户端和服务器使用JSON-RPC消息格式进行通信
4. 消息通过HTTP连接流式传输(通常使用HTTP/1.1的分块传输或HTTP/2的流)

虽然理论上可以使用一个双向通道，但分离读写流使API更清晰、更灵活，也更容易扩展到其他传输机制。

## 总结

MCP SDK使用独立的读写流是一个有意的设计选择，为了:

1. 提供通用抽象，适用于多种传输协议
2. 支持真正的异步操作和并发通信
3. 允许独立的流控制和缓冲区管理
4. 提供一致的API，不管底层传输机制如何

这种设计虽然初看起来可能显得复杂，但它使SDK能够以一致的方式支持多种传输方式，同时保持高度的灵活性和可扩展性。

zhkzly: 我现在已经理解客户端了，请按照之前介绍客户端的过程介绍 服务端，需要给出详细的解释

GitHub Copilot: # MCP Python SDK 服务端部分解析

为了详细介绍MCP Python SDK的服务端实现，我将分析其核心类、继承关系、关键功能和使用方式。首先，让我搜索一些关键服务端代码以便能够提供更全面的解析。 让我获取一些其他相关的文件来更好地理解MCP服务端的关键组件： 基于我收集的信息，现在我可以详细解析MCP Python SDK的服务端部分了。

# MCP Python SDK 服务端部分解析

## 核心类及继承关系

在MCP服务端中，有几个关键类：

1. **ServerSession**: 这是服务端的主要会话类，处理与客户端的交互
2. **BaseSession**: `ServerSession` 继承自这个基类，提供通用会话功能
3. **FastMCP**: 高级API，简化MCP服务器的创建和配置
4. **Server** (MCPServer): 底层服务器实现，由FastMCP内部使用
5. **Context**: 请求上下文对象，提供工具函数访问服务资源

继承关系图：
```
BaseSession
    └── ServerSession

Server (MCPServer) ──────┐
                         │
                  使用   │
                         ▼
Tool ───┐          ┌── FastMCP
         │         │
Resource ┼── 管理 ─┤     
         │         │
Prompt ──┘         └── Context
```

## 关键类详解

### 1. ServerSession - 服务端会话

```python
class ServerSession(
    BaseSession[
        types.ServerRequest,
        types.ServerNotification,
        types.ServerResult,
        types.ClientRequest,
        types.ClientNotification,
    ]
):
    # ...
```

**功能**: 管理服务端和客户端之间的通信会话，处理请求/响应循环。

**关键方法**:
- `__init__`: 初始化会话，设置读写流和初始化选项
- `_received_request`: 处理来自客户端的请求
- `_received_notification`: 处理来自客户端的通知
- `send_resource_list_changed`: 发送资源列表变更通知
- `send_tool_list_changed`: 发送工具列表变更通知

**泛型参数说明**:
- `ServerRequest`: 服务端发送的请求类型
- `ServerNotification`: 服务端发送的通知类型
- `ServerResult`: 服务端发送的结果类型
- `ClientRequest`: 接收的客户端请求类型
- `ClientNotification`: 接收的客户端通知类型

### 2. FastMCP - 高级服务端API

```python
class FastMCP:
    def __init__(
        self,
        name: str | None = None,
        instructions: str | None = None,
        auth_server_provider: OAuthAuthorizationServerProvider[Any, Any, Any] | None = None,
        event_store: EventStore | None = None,
        *,
        tools: list[Tool] | None = None,
        **settings: Any,
    ):
        # ...
```

**功能**: 提供简洁的API来创建和配置MCP服务器，管理各种资源、工具和提示。

**关键方法与装饰器**:
- `tool()`: 装饰器，将函数注册为工具
- `resource()`: 装饰器，将函数注册为资源
- `prompt()`: 装饰器，将函数注册为提示模板
- `run()`: 运行服务器，支持不同传输协议
- `sse_app()`: 创建SSE传输的Starlette应用
- `streamable_http_app()`: 创建Streamable HTTP传输的Starlette应用
- `custom_route()`: 添加自定义API路由

**示例用法**:
```python
mcp = FastMCP("Echo Server")

@mcp.tool()
def echo(text: str) -> str:
    """Echo the input text"""
    return text

@mcp.resource("echo://{text}")
def echo_resource(text: str) -> str:
    return f"Echo: {text}"

mcp.run(transport="streamable-http")
```

### 3. Context - 工具上下文

```python
class Context(BaseModel, Generic[ServerSessionT, LifespanContextT]):
    # ...
```

**功能**: 提供上下文对象，让工具和资源访问会话、请求信息和服务器功能。

**关键方法**:
- `report_progress()`: 报告进度更新
- `read_resource()`: 读取资源内容
- `log()`, `debug()`, `info()`, `warning()`, `error()`: 日志记录
- `session`: 访问底层会话
- `request_id`: 获取请求ID

**示例用法**:
```python
@mcp.tool()
async def tool_with_progress(message: str, ctx: Context, steps: int = 3) -> str:
    await ctx.info(f"Starting processing of '{message}'")
    
    for i in range(steps):
        await ctx.report_progress(
            progress=(i + 1) / steps,
            total=1.0,
            message=f"Processing step {i + 1} of {steps}",
        )
    
    return f"Processed '{message}' in {steps} steps"
```

## 服务端核心功能

### 1. 工具管理 (Tool Management)

工具是通过 `ToolManager` 管理的，它们表示可以由客户端调用的函数：

```python
@mcp.tool()
def calculate_bmi(weight_kg: float, height_m: float) -> float:
    """Calculate BMI given weight in kg and height in meters"""
    return weight_kg / (height_m**2)
```

工具支持:
- 自动参数验证和转换
- 异步和同步函数
- 通过 Context 参数访问会话状态和上下文
- 进度报告和日志记录

### 2. 资源管理 (Resource Management)

资源通过 `ResourceManager` 管理，它们表示可以被客户端读取的数据：

```python
@mcp.resource("resource://static/info")
def get_static_info() -> str:
    return "This is static resource content"

@mcp.resource("resource://dynamic/{category}")
def dynamic_resource(category: str) -> str:
    return f"Dynamic resource content for category: {category}"
```

资源支持:
- 静态资源
- 动态URL模板
- 不同的MIME类型和二进制数据

### 3. 提示管理 (Prompt Management)

提示通过 `PromptManager` 管理，定义LLM交互模板：

```python
@mcp.prompt(description="A simple prompt")
def simple_prompt(topic: str) -> str:
    return f"Tell me about {topic}"
```

### 4. 传输协议支持

FastMCP支持多种传输协议：

1. **stdio**: 使用标准输入/输出进行通信，适用于本地开发
   ```python
   mcp.run(transport="stdio")
   ```

2. **SSE (Server-Sent Events)**: 用于长连接Web应用
   ```python
   mcp.run(transport="sse")
   ```

3. **Streamable HTTP**: 更现代的HTTP流式传输
   ```python
   mcp.run(transport="streamable-http")
   ```

### 5. 认证和授权

FastMCP支持OAuth认证：

```python
auth_settings = AuthSettings(
    issuer_url="http://localhost:8000",
    client_registration_options=ClientRegistrationOptions(
        enabled=True,
        valid_scopes=["mcp"],
        default_scopes=["mcp"],
    ),
    required_scopes=["mcp"],
)

app = FastMCP(
    name="Auth Server",
    auth_server_provider=oauth_provider,
    auth=auth_settings,
)
```

## 请求处理流程

1. 客户端通过传输协议连接到服务器
2. 服务器创建ServerSession实例处理连接
3. 客户端发送初始化请求
4. 服务器响应能力和版本信息
5. 会话开始接收处理请求/通知：
   - 工具调用 (call_tool)
   - 资源读取 (read_resource)
   - 提示获取 (get_prompt)
6. 服务器可能发送进度通知和日志消息
7. 最终客户端断开连接或会话超时

## 服务端泛型机制

与客户端类似，服务端也使用泛型机制来确保类型安全：

```python
class ServerSession(
    BaseSession[
        types.ServerRequest,
        types.ServerNotification,
        types.ServerResult,
        types.ClientRequest,
        types.ClientNotification,
    ]
):
    # ...
```

ServerSession类型参数的方向与ClientSession相反，因为：
- ServerSession发送ServerRequest、ServerNotification、ServerResult
- ServerSession接收ClientRequest、ClientNotification

## 高级功能

### 1. 生命周期管理 (Lifespan)

FastMCP支持生命周期钩子，用于资源初始化和清理：

```python
@contextlib.asynccontextmanager
async def lifespan(app: FastMCP):
    # 建立连接
    db = await setup_database()
    # 将上下文传递给工具和资源
    yield {"db": db}
    # 清理资源
    await db.close()

mcp = FastMCP("My App", lifespan=lifespan)
```

### 2. 进度报告

服务端可以发送进度更新：

```python
async def long_running_task(ctx: Context) -> str:
    total_steps = 10
    for i in range(total_steps):
        # 执行工作
        await process_step(i)
        # 报告进度
        await ctx.report_progress(
            progress=(i+1)/total_steps,
            total=1.0,
            message=f"步骤 {i+1}/{total_steps} 完成"
        )
    return "任务完成"
```

### 3. 日志和通知

服务端可以发送日志和系统通知：

```python
async def complex_tool(ctx: Context) -> str:
    await ctx.debug("调试信息")
    await ctx.info("开始处理")
    await ctx.warning("潜在问题")
    await ctx.error("发生错误")
    return "操作完成"
```

## 总结

MCP SDK的服务端组件提供了一个强大而灵活的框架来构建LLM上下文服务器：

1. **类型安全**: 使用泛型和Pydantic确保消息处理的类型安全
2. **灵活的API**: FastMCP提供简洁的API创建各种服务器组件
3. **多种传输协议**: 支持stdio、SSE和Streamable HTTP
4. **可扩展性**: 从简单示例到复杂的企业级应用都可以构建
5. **认证集成**: 内置OAuth支持确保安全访问

服务端核心是`ServerSession`，它处理底层通信，而`FastMCP`提供了更高级别的抽象，大大简化了服务器的创建和配置。`Context`对象将请求信息和服务器功能暴露给工具和资源处理函数。

这种设计使得开发者能够快速构建功能丰富的MCP服务器，而不必担心底层协议和消息处理的复杂性。

zhkzly: class Context(BaseModel, Generic[ServerSessionT, LifespanContextT]):
    这个对象具体在服务器端有什么作用？？请具体讲解，并给出示例

GitHub Copilot: # Context 对象在 MCP 服务端的作用

`Context` 对象是 MCP 服务端的一个核心组件，它在 FastMCP 框架中扮演着非常重要的角色。我来详细解释它的作用及用法。

## Context 对象的基本功能

`Context` 对象是一个连接工具函数与底层 MCP 服务器功能的桥梁。它为工具函数（tools）、资源函数（resources）和提示函数（prompts）提供访问以下功能的能力：

1. **请求上下文**：访问当前请求的元数据和参数
2. **会话信息**：访问客户端会话数据和连接状态
3. **资源访问**：读取其他资源内容
4. **日志记录**：发送不同级别的日志消息
5. **进度报告**：报告长时间运行任务的进度
6. **生命周期上下文**：访问在服务器启动时初始化的共享资源

## Context 对象的泛型参数

```python
class Context(BaseModel, Generic[ServerSessionT, LifespanContextT]):
    # ...
```

- **ServerSessionT**: 服务器会话的类型，通常是 `ServerSession`
- **LifespanContextT**: 生命周期上下文的类型，这是在服务器启动时创建的对象类型

## Context 对象的主要方法和属性

### 1. 进度报告方法

```python
async def report_progress(
    self, progress: float, total: float | None = None, message: str | None = None
) -> None
```

报告长时间运行任务的进度，让客户端可以显示进度条或其他进度指示器。

### 2. 日志记录方法

```python
async def log(
    self,
    level: Literal["debug", "info", "warning", "error"],
    message: str,
    *,
    logger_name: str | None = None,
) -> None

async def debug(self, message: str, **extra: Any) -> None
async def info(self, message: str, **extra: Any) -> None
async def warning(self, message: str, **extra: Any) -> None
async def error(self, message: str, **extra: Any) -> None
```

发送各级别的日志消息到客户端，客户端可以根据配置显示或记录这些消息。

### 3. 资源访问方法

```python
async def read_resource(self, uri: str | AnyUrl) -> Iterable[ReadResourceContents]
```

读取资源内容，例如获取其他资源的数据。

### 4. 会话信息属性

```python
@property
def session(self) -> ServerSessionT
```

访问底层的服务器会话对象。

### 5. 请求和客户端信息

```python
@property
def client_id(self) -> str | None

@property
def request_id(self) -> str
```

获取客户端标识符和请求ID。

## 实际示例

下面通过几个实际的用例来展示`Context`对象的常见用法：

### 示例1：进度报告和日志记录

```python
from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP("Data Processing Server")

@mcp.tool()
async def process_data(dataset_id: str, ctx: Context) -> str:
    """处理指定的数据集并报告进度"""
    
    await ctx.info(f"开始处理数据集 {dataset_id}")
    
    # 模拟数据处理步骤
    total_steps = 5
    for i in range(total_steps):
        # 数据处理逻辑
        await ctx.debug(f"执行处理步骤 {i+1}")
        
        # 报告进度
        progress = (i + 1) / total_steps
        await ctx.report_progress(
            progress=progress,
            total=1.0,
            message=f"处理步骤 {i+1}/{total_steps}"
        )
        
        # 如果出现问题，可以记录警告
        if i == 2:
            await ctx.warning("发现潜在数据质量问题，但可以继续处理")
    
    await ctx.info(f"数据集 {dataset_id} 处理完成")
    return f"成功处理了数据集 {dataset_id}"
```

### 示例2：资源访问和共享上下文

```python
from mcp.server.fastmcp import FastMCP, Context
import contextlib
from typing import TypedDict

# 定义生命周期上下文类型
class AppContext(TypedDict):
    database: object

# 创建应用生命周期管理器
@contextlib.asynccontextmanager
async def app_lifespan(app: FastMCP):
    # 初始化共享资源
    print("初始化数据库连接")
    db = {"users": {"alice": {"role": "admin"}, "bob": {"role": "user"}}}
    
    # 提供给所有工具和资源使用的上下文
    yield {"database": db}
    
    # 清理资源
    print("关闭数据库连接")

# 创建FastMCP实例，使用我们的生命周期管理器
mcp = FastMCP("用户管理系统", lifespan=app_lifespan)

# 定义一个资源提供用户信息
@mcp.resource("users://{user_id}/profile")
def get_user_profile(user_id: str) -> str:
    """获取用户资料"""
    return f"用户 {user_id} 的个人资料"

# 定义一个需要访问资源和数据库的工具
@mcp.tool()
async def validate_user_permission(user_id: str, resource_id: str, ctx: Context[ServerSession, AppContext]) -> str:
    """检查用户是否有权限访问资源"""
    
    # 访问数据库（通过生命周期上下文）
    db = ctx.request_context.lifespan_context["database"]
    
    # 记录操作
    await ctx.info(f"检查用户 {user_id} 访问资源 {resource_id} 的权限")
    
    # 从数据库获取用户信息
    if user_id not in db["users"]:
        await ctx.error(f"用户 {user_id} 不存在")
        return f"错误: 用户 {user_id} 不存在"
    
    # 获取用户角色
    user_role = db["users"][user_id]["role"]
    
    # 获取用户资料资源
    try:
        profile_uri = f"users://{user_id}/profile"
        profile_content = await ctx.read_resource(profile_uri)
        await ctx.debug(f"已加载用户资料: {profile_content}")
    except Exception as e:
        await ctx.error(f"无法加载用户资料: {e}")
    
    # 根据角色决定权限
    if user_role == "admin":
        await ctx.info(f"授予用户 {user_id} 访问资源 {resource_id} 的权限 (管理员)")
        return f"允许: 用户 {user_id} (管理员) 可以访问资源 {resource_id}"
    elif resource_id.startswith(f"users/{user_id}"):
        await ctx.info(f"授予用户 {user_id} 访问个人资源的权限")
        return f"允许: 用户 {user_id} 可以访问个人资源 {resource_id}"
    else:
        await ctx.warning(f"拒绝用户 {user_id} 访问资源 {resource_id} (权限不足)")
        return f"拒绝: 用户 {user_id} 没有访问资源 {resource_id} 的权限"
```

### 示例3：客户端信息和高级会话功能

```python
from mcp.server.fastmcp import FastMCP, Context
from mcp.types import TextContent, SamplingMessage

mcp = FastMCP("AI助手系统")

@mcp.tool()
async def generate_response(prompt: str, ctx: Context) -> str:
    """使用LLM生成响应"""
    
    # 获取客户端和请求信息
    client_id = ctx.client_id
    request_id = ctx.request_id
    
    await ctx.info(f"客户端 {client_id} 发送请求 {request_id}")
    
    # 使用客户端的LLM能力生成回复
    try:
        result = await ctx.session.create_message(
            messages=[
                SamplingMessage(
                    role="user", 
                    content=TextContent(type="text", text=prompt)
                )
            ],
            max_tokens=100,
            temperature=0.7,
        )
        
        await ctx.info("成功从LLM获取回复")
        return f"AI回复: {result.content.text if result.content.type == 'text' else str(result.content)}"
        
    except Exception as e:
        await ctx.error(f"LLM生成失败: {e}")
        return f"抱歉，生成回复时出现错误: {str(e)}"
```

## Context 对象的价值

`Context` 对象提供了几个关键优势:

1. **简化访问**: 工具函数无需直接了解底层协议和服务器实现就能访问关键功能
2. **类型安全**: 通过泛型参数提供类型安全的访问
3. **统一接口**: 为日志、进度报告等常见功能提供统一接口
4. **资源共享**: 通过生命周期上下文在不同请求间共享数据库连接等资源
5. **会话访问**: 提供对当前会话状态和客户端信息的访问

总之，`Context` 对象在MCP服务端是一个强大的工具，它使工具函数、资源函数和提示函数能够访问底层服务器功能，同时保持简洁易用的接口。它是连接应用业务逻辑和MCP协议实现的关键桥梁。

zhkzly: from mcp.server.fastmcp import FastMCP, Context
from mcp.types import TextContent, SamplingMessage

mcp = FastMCP("AI助手系统")

@mcp.tool()
async def generate_response(prompt: str, ctx: Context) -> str:
    """使用LLM生成响应"""
    
    # 获取客户端和请求信息
    client_id = ctx.client_id
    request_id = ctx.request_id
    
    await ctx.info(f"客户端 {client_id} 发送请求 {request_id}")
    
    # 使用客户端的LLM能力生成回复
    try:
        result = await ctx.session.create_message(
            messages=[
                SamplingMessage(
                    role="user", 
                    content=TextContent(type="text", text=prompt)
                )
            ],
            max_tokens=100,
            temperature=0.7,
        )
        
        await ctx.info("成功从LLM获取回复")
        return f"AI回复: {result.content.text if result.content.type == 'text' else str(result.content)}"
        
    except Exception as e:
        await ctx.error(f"LLM生成失败: {e}")
        return f"抱歉，生成回复时出现错误: {str(e)}"

        create_message是和谁进行数据传输？？

GitHub Copilot: # `create_message` 方法解析：谁在提供LLM生成能力？

`create_message` 方法是一个很特殊的MCP功能，它实际上是在**向客户端**请求执行LLM生成，而不是服务器自己生成内容。这是MCP协议中一个重要的设计理念，让我来详细解释：

## `create_message` 数据流向

在你的示例代码中：

```python
result = await ctx.session.create_message(
    messages=[
        SamplingMessage(
            role="user", 
            content=TextContent(type="text", text=prompt)
        )
    ],
    max_tokens=100,
    temperature=0.7,
)
```

数据传输流程如下：

1. **服务器 → 客户端**: 服务器发送一个`CreateMessageRequest`请求给客户端
2. **客户端处理**: 客户端收到请求后调用其关联的LLM模型生成文本
3. **客户端 → 服务器**: 客户端将生成结果作为`CreateMessageResult`返回给服务器
4. **服务器继续**: 服务器获取生成结果并在工具函数中使用

## 为什么是这样设计的？

这种反向调用的设计有几个重要优势：

1. **解耦模型与工具**: 服务器专注于提供工具和资源，不需要直接实现AI模型
2. **客户端控制**: 客户端可以控制使用哪个模型以及如何调用它
3. **隐私保护**: 敏感提示内容可以在客户端本地处理，无需发送到第三方API
4. **灵活性**: 不同客户端可以使用不同的模型实现，服务器代码无需更改

## 实际工作原理

在MCP架构中:

1. **服务器端工具**请求生成文本
2. 请求通过**MCP协议**发送给客户端
3. **客户端**接收到请求并处理:
   ```
   ClientSession._received_request() 
   → _sampling_callback()
   → 调用实际的LLM API或本地模型
   ```
4. 客户端获得结果后回传给服务器
5. 服务器工具获得结果并继续执行

## 真实场景示例

以Claude Desktop作为客户端的情况为例：

1. 你的MCP服务器运行工具代码，调用`create_message`
2. Claude Desktop客户端接收到这个请求
3. Claude Desktop调用Anthropic的Claude API生成回复
4. 生成的回复被发送回你的MCP服务器
5. 你的MCP服务器工具继续处理这个生成的文本

在CLI场景下：

1. `mcp` CLI工具充当客户端
2. 当接收到`create_message`请求时，它可能调用OpenAI、Anthropic或其他配置的API
3. 或显示一个提示让人类用户输入回复

## 客户端如何实现LLM调用

客户端需要实现一个`sampling_callback`函数来处理`CreateMessageRequest`。例如：

```python
async def handle_sampling(
    context: RequestContext,
    params: types.CreateMessageRequestParams,
) -> types.CreateMessageResult:
    # 调用OpenAI API
    completion = await openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": msg.role, "content": msg.content.text} 
                  for msg in params.messages],
        max_tokens=params.maxTokens,
        temperature=params.temperature,
    )
    
    # 返回结果给服务器
    return types.CreateMessageResult(
        role="assistant",
        content=types.TextContent(
            type="text",
            text=completion.choices[0].message.content,
        ),
        model="gpt-4",
        stopReason="endTurn",
    )
```

这个回调函数通常在创建ClientSession时提供：

```python
client_session = ClientSession(
    read_stream, 
    write_stream,
    sampling_callback=handle_sampling
)
```

## 总结

`create_message`是一种从**服务器向客户端请求LLM生成**的方法，这反转了通常的客户端-服务器关系。这种设计使得MCP服务器可以专注于提供工具和资源，而将AI模型的选择和控制权留给客户端。

这种架构对于构建AI生态系统非常强大，因为它允许工具开发者（服务器端）和AI模型提供者（客户端）独立工作，同时通过标准化协议实现无缝集成。

zhkzly: @mcp.resource("users://{user_id}/profile")。定义资源的时候，这个路径是什么意思？？

GitHub Copilot: # MCP 资源路径的含义与用法

在 MCP (Model Context Protocol) 中，`@mcp.resource("users://{user_id}/profile")` 这样的路径定义是一个资源 URI 模板，它具有特定的意义和作用。让我来详细解释:

## 资源路径的基本概念

`"users://{user_id}/profile"` 是一个资源 URI 模板，它包含以下几个部分:

1. **方案 (Scheme)**: `users://` 
2. **路径参数**: `{user_id}` 是一个参数占位符
3. **路径部分**: `/profile` 是资源路径的固定部分

## 资源 URI 的作用

资源 URI 在 MCP 中具有三个主要作用:

### 1. 唯一标识资源

URI 是客户端引用和访问资源的唯一标识符。例如，客户端可以通过 `"users://alice/profile"` 来请求特定用户的资料。

### 2. 参数传递

URI 模板中的 `{user_id}` 部分定义了一个动态参数，它将:
- 接收客户端请求中的值 (例如 `"users://alice/profile"`)
- 作为参数传递给资源函数 (对应函数参数 `user_id`)

### 3. 资源组织

URI 方案和路径提供了一种逻辑组织资源的方式，类似文件系统或 REST API:
- `users://` 表明这是与用户相关的资源
- `/profile` 指明这是用户的个人资料资源

## URI 方案命名规则

方案部分 (例如 `users://`) 不是预定义的标准协议 (不同于 `http://`、 等)，而是由应用程序开发者自由定义的命名空间。这些是应用程序特定的命名空间，用于组织和分类资源。

一些常见的命名模式:

-  - 文件系统资源
- `db://` - 数据库资源
- `api://` - 外部 API 资源
- `users://` - 用户相关资源
- `config://` - 配置相关资源
- `docs://` - 文档相关资源

## 资源函数与 URI 的关系

当你定义像这样的资源:

```python
@mcp.resource("users://{user_id}/profile")
def get_user_profile(user_id: str) -> str:
    """获取用户资料"""
    return f"用户 {user_id} 的个人资料"
```

以下是发生的事情:

1. MCP 将该函数注册为资源处理程序
2. MCP 解析 URI 模板并提取参数 (`user_id`)
3. MCP 验证函数参数与 URI 参数匹配
4. 当客户端请求资源时:
   - MCP 根据 URI 找到匹配的资源处理程序
   - 从 URI 中提取参数值
   - 调用处理函数并传递这些参数
   - 返回函数结果作为资源内容

## 实际示例

### 基本资源示例

```python
# 静态资源 - 没有参数
@mcp.resource("config://app/settings")
def get_settings() -> str:
    return "应用程序设置内容"

# 单参数资源
@mcp.resource("products://{product_id}")
def get_product(product_id: str) -> str:
    return f"产品 {product_id} 的信息"

# 多参数资源
@mcp.resource("docs://{category}/{doc_id}")
def get_document(category: str, doc_id: str) -> str:
    return f"{category} 类别中文档 {doc_id} 的内容"
```

### 参数类型转换

```python
# 整数参数
@mcp.resource("items://{item_id}/details")
def get_item_details(item_id: int) -> str:
    # item_id 会自动从字符串转换为整数
    return f"商品 #{item_id} 的详细信息"
```

### 高级用法

```python
# 返回二进制数据的资源
@mcp.resource("images://{image_id}", mime_type="image/png")
def get_image(image_id: str) -> bytes:
    # 从数据库或文件系统获取图像数据
    return get_image_data(image_id)

# 异步资源
@mcp.resource("weather://{city}")
async def get_weather(city: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://weather-api.example.com/{city}")
        data = response.json()
        return f"{city} 的天气: {data['temperature']}°C, {data['condition']}"
```

## 客户端如何访问这些资源

客户端通过 `read_resource` 方法访问资源:

```python
# 客户端代码
content, mime_type = await client_session.read_resource("users://alice/profile")
print(f"用户资料: {content}")

# 在工具内部通过 Context 访问
@mcp.tool()
async def analyze_user(user_id: str, ctx: Context) -> str:
    profile_data, _ = await ctx.read_resource(f"users://{user_id}/profile")
    return f"分析结果: 用户 {user_id} 资料中包含 {len(profile_data)} 个字符"
```

## 总结

资源 URI 是 MCP 的一个关键概念，它:

1. 提供了清晰的命名空间和路径结构来组织各种资源
2. 支持动态参数，将 URI 组件映射到函数参数
3. 让客户端和服务端工具能够通过一致的方式引用和访问资源
4. 创建了一个类似文件系统或 REST API 的抽象，但专为 LLM 上下文设计

在创建 MCP 应用程序时，设计良好的资源 URI 结构可以让你的应用更容易理解和维护，同时为客户端应用程序和 LLM 提供直观的资源访问方式。

zhkzly: 本质上就是自己定义的一个说明符？

GitHub Copilot: # MCP 资源 URI：本质与作用

是的，你理解得非常准确！在 MCP 中，资源 URI（如 `"users://{user_id}/profile"`）本质上就是一个**自定义的资源标识符**或者说**说明符**。它并不依赖于现有的标准协议或系统，而是由 MCP 框架定义和解析的一种约定。

## 资源 URI 的本质

这些 URI 本质上是：

1. **自定义命名约定**：开发者可以根据自己的需求和偏好定义任何命名方案
   
2. **虚拟路径系统**：类似于文件系统的路径，但完全是虚拟的，不一定对应实际文件

3. **结构化标识符**：为资源提供结构化的命名和组织方式

4. **参数化模板**：包含可替换的参数部分，用于动态资源访问

## 与其他识别符的比较

| 标识符系统 | 示例 | MCP 资源 URI 的区别 |
|------------|------|-------------------|
| 文件路径 | `/home/user/file.txt` | MCP URI 是虚拟的，不需要对应实际文件 |
| HTTP URL | `https://example.com/api/users/123` | MCP URI 没有主机名，仅用于应用内识别 |
| URN | `urn:isbn:0451450523` | MCP URI 更类似于路径，包含参数化部分 |

## 关键特点总结

1. **纯粹的约定**：没有注册的标准方案名称，完全由应用开发者定义

2. **简单解析**：使用简单的字符串替换和模式匹配来处理参数

3. **应用内部使用**：主要用于 MCP 框架内部的资源标识和路由

4. **直观易懂**：便于开发者和 LLM 理解资源的组织结构

5. **灵活可扩展**：可以根据应用需求定义任意的命名方案和路径结构

## 简化理解

如果要进一步简化，你可以将 MCP 资源 URI 视为：

> 一个有结构的字符串模板，用来匹配客户端请求和标识服务器资源，其中包含固定部分和可变参数部分。

这个简单的约定让 MCP 能够以一种直观的方式组织和识别不同类型的资源，而不需要依赖复杂的路由系统或外部标准。

所以从技术实现角度看，它确实就是一个自定义的说明符/标识符系统，但这种简单性正是 MCP 设计的优势之一，让资源定义和访问变得非常直观和灵活。

zhkzly: shared 文件夹中的内容都是什么？？请详细介绍

GitHub Copilot: # MCP Python SDK 中 `shared` 文件夹的详细介绍

让我首先用搜索工具获取 `shared` 文件夹中的文件列表，然后详细介绍其内容和功能。 让我查看其中几个主要文件的内容来了解它们的功能： 根据收集到的信息，我将详细介绍MCP Python SDK中的`shared`文件夹内容及其功能。

# MCP Python SDK中的`shared`文件夹详细介绍

`shared`文件夹包含了MCP SDK中被客户端和服务器端共同使用的核心组件，它提供了基础设施和工具，使得客户端和服务器端能够以一致的方式处理MCP协议的通信、会话管理和其他共享功能。这种模块化设计使得代码可以被重用，并确保了客户端和服务器之间的兼容性。

## 核心文件及其功能

### 1. session.py - 会话管理

这是整个MCP架构中最核心的文件之一，实现了`BaseSession`类，为客户端和服务器会话提供共同的基础功能：

- 定义了通用的会话管理接口
- 实现了请求/响应机制
- 处理消息队列和传输
- 提供了泛型支持，使得客户端和服务器会话可以共享相同的基础实现
- 包含了消息发送和接收的核心逻辑

`BaseSession`包含的泛型定义:
```python
SendRequestT = TypeVar("SendRequestT", ClientRequest, ServerRequest)
SendResultT = TypeVar("SendResultT", ClientResult, ServerResult)
SendNotificationT = TypeVar("SendNotificationT", ClientNotification, ServerNotification)
ReceiveRequestT = TypeVar("ReceiveRequestT", ClientRequest, ServerRequest)
ReceiveResultT = TypeVar("ReceiveResultT", bound=BaseModel)
ReceiveNotificationT = TypeVar("ReceiveNotificationT", ClientNotification, ServerNotification)
```

### 2. context.py - 请求上下文

提供请求上下文功能，使服务器能够在处理请求时访问必要的上下文信息：

```python
@dataclass
class RequestContext(Generic[SessionT, LifespanContextT]):
    request_id: RequestId
    meta: RequestParams.Meta | None
    session: SessionT
    lifespan_context: LifespanContextT
```

- 存储当前请求的ID、元数据和会话信息
- 通过泛型支持不同类型的会话和生命周期上下文
- 使工具函数能够访问共享的应用状态和资源

### 3. memory.py - 内存传输

为测试和开发提供内存中的传输实现：

- 创建客户端和服务器之间的内存通信通道
- 允许在测试中模拟MCP会话而无需实际的网络连接
- 提供了用于创建内存流的工具函数
- 包含连接客户端和服务器会话的助手函数

其中一个主要函数是：
```python
@asynccontextmanager
async def create_client_server_memory_streams() -> AsyncGenerator[tuple[MessageStream, MessageStream], None]
```

这个函数创建了两对流，一对用于客户端，一对用于服务器，使它们可以相互通信。

### 4. message.py - 消息封装

定义了用于传输和处理消息的类型：

```python
@dataclass
class ClientMessageMetadata:
    """Metadata specific to client messages."""
    # ...

@dataclass
class ServerMessageMetadata:
    """Metadata specific to server messages."""
    # ...

@dataclass
class SessionMessage:
    """A message with optional metadata."""
    # ...
```

- 包装JSON-RPC消息以支持元数据
- 实现了支持会话恢复的功能
- 提供了客户端和服务器特定元数据类型

### 5. exceptions.py - 异常处理

定义了MCP协议的异常类型：

```python
class McpError(Exception):
    """Exception type raised when an error arrives over an MCP connection."""
    error: ErrorData
    # ...
```

这个类封装了在MCP通信中发生的错误，使错误处理更加统一和可预测。

### 6. auth.py - 认证共享组件

实现了客户端和服务器共享的认证相关类型和功能：

- OAuth认证的共享模型
- 令牌和客户端信息数据结构
- 认证相关的工具函数和助手

### 7. progress.py - 进度通知

提供用于进度报告和跟踪的功能：

- 进度通知模型
- 上下文管理器，简化进度更新
- 用于报告长时间运行操作进度的工具

### 8. _httpx_utils.py - HTTP工具

包含用于创建标准化HTTP客户端的工具：

```python
def create_mcp_http_client(
    headers: dict[str, str] | None = None,
    timeout: httpx.Timeout | None = None,
    auth: httpx.Auth | None = None,
) -> httpx.AsyncClient:
    # ...
```

- 提供HTTP请求的工具函数
- 设置默认超时和标准头信息
- 用于与外部API交互

### 9. version.py - 版本管理

管理MCP协议版本兼容性：

```python
SUPPORTED_PROTOCOL_VERSIONS: list[str] = ["2024-11-05", LATEST_PROTOCOL_VERSION]
```

存储支持的协议版本列表，并提供版本检查逻辑，确保客户端和服务器使用兼容的协议版本。

## 功能和设计理念

`shared`文件夹的设计体现了几个关键概念：

### 1. 代码重用

客户端和服务器共享大量的底层逻辑，包括会话管理、消息处理和序列化。通过将这些共同功能提取到`shared`模块，减少了重复代码并确保了一致的行为。

### 2. 协议一致性

确保客户端和服务器以完全相同的方式解释MCP协议，通过共享类型定义和消息处理逻辑。

### 3. 泛型编程

使用TypeVar和泛型类型，创建了可以在客户端和服务器之间共享的基础类，同时保持类型安全，例如：

```python
class BaseSession(
    Generic[
        SendRequestT,
        SendNotificationT,
        SendResultT,
        ReceiveRequestT,
        ReceiveNotificationT,
    ]
):
    # ...
```

### 4. 关注点分离

将实现与协议定义分开，使得代码更易于理解和维护：
- types.py（不在shared文件夹中）定义协议类型
- `shared`目录中的文件提供实现细节

## 使用场景示例

### 测试和开发场景

```python
# 使用memory.py创建内存传输并连接客户端和服务器
async with create_connected_server_and_client_session(server) as client_session:
    # 使用客户端会话进行测试
    await client_session.initialize()
    result = await client_session.call_tool("echo", {"text": "Hello world"})
```

### 错误处理

```python
try:
    result = await session.call_tool("some_tool", args)
except McpError as e:
    # 使用共享的异常类型处理错误
    print(f"错误代码: {e.error.code}, 消息: {e.error.message}")
```

### 进度报告

```python
# 在服务器工具中使用共享的进度机制
with progress(ctx, total=100.0) as progress_ctx:
    for i in range(10):
        # 执行工作...
        progress_ctx.update(10.0, message=f"步骤 {i+1}/10 完成")
```

## 总结

`shared`文件夹包含了MCP SDK客户端和服务器组件之间共享的核心功能。这种架构设计体现了代码重用、协议一致性和关注点分离等良好的软件工程实践。它通过提供统一的会话管理、消息处理和工具函数，使得MCP客户端和服务器能够无缝地协同工作，同时仍然保持各自的职责和特性。

这些共享组件为MCP的实现提供了坚实的基础，是整个SDK的重要核心，确保了协议实现的正确性和一致性，同时简化了开发和测试过程。

zhkzly: memory是干什么的？请给出详细的介绍

GitHub Copilot: # MCP Python SDK 中的 memory.py 详细解析

让我仔细查看 memory.py 的完整内容，以提供更详细的介绍： 让我查看一下相关的测试用例，以更好地理解其用法和功能： 现在我可以提供详细的介绍了：

# MCP Python SDK 中的 memory.py 详细介绍

MCP Python SDK 中的 memory.py 是一个专门用于在内存中创建和管理通信流的模块，它提供了一种无需实际网络连接就能在客户端和服务器组件之间进行通信的机制。这个模块主要服务于以下场景：单元测试、集成测试和开发环境，让开发者能够快速验证 MCP 客户端和服务器的交互而无需设置真实的网络传输。

## 核心功能与实现

### 1. 内存流创建

模块的核心功能是创建内存中的消息流，用于在客户端和服务器之间传递消息：

```python
@asynccontextmanager
async def create_client_server_memory_streams() -> AsyncGenerator[tuple[MessageStream, MessageStream], None]:
    # ...
```

这个函数创建了两对双向流：
- **客户端流**: (读取从服务器发来的消息, 向服务器写入消息)
- **服务器流**: (读取从客户端发来的消息, 向客户端写入消息)

关键实现细节：
- 使用 `anyio.create_memory_object_stream` 创建内存队列
- 设计为异步上下文管理器，确保资源正确清理
- 创建容量为 1 的流，模拟真实的消息传递行为（消息必须被处理后才能发送下一条）

### 2. 连接客户端与服务器会话

memory.py 最有价值的功能是 `create_connected_server_and_client_session`：

```python
@asynccontextmanager
async def create_connected_server_and_client_session(
    server: Server[Any],
    read_timeout_seconds: timedelta | None = None,
    sampling_callback: SamplingFnT | None = None,
    list_roots_callback: ListRootsFnT | None = None,
    logging_callback: LoggingFnT | None = None,
    message_handler: MessageHandlerFnT | None = None,
    client_info: types.Implementation | None = None,
    raise_exceptions: bool = False,
) -> AsyncGenerator[ClientSession, None]:
    # ...
```

这个函数可以：
- 接收一个 `Server` 实例
- 创建内存通信流
- 启动服务器在一个后台任务中运行
- 创建并初始化客户端会话
- 返回已连接并初始化的客户端会话，供测试使用
- 在上下文退出时自动清理资源（取消服务器任务等）

### 3. 消息类型和流定义

```python
MessageStream = tuple[
    MemoryObjectReceiveStream[SessionMessage | Exception],
    MemoryObjectSendStream[SessionMessage],
]
```

这个类型定义表示一个消息流对，包含：
- 接收流：可以接收 `SessionMessage` 或 `Exception`
- 发送流：用于发送 `SessionMessage`

支持异常传递是一个重要特性，允许传输层错误被正确处理和传播。

## 工作原理详解

### 内存流的建立和连接方式

memory.py 使用了一种巧妙的方式来创建在内存中互连的客户端和服务器：

1. **双向连接创建**:
   ```
   Client                 Server
     ┌─────┐ write   read ┌─────┐
     │     │───────────-->│     │
     │     │               │     │
     │     │ read    write │     │
     │     │<─────────────│     │
     └─────┘               └─────┘
   ```

2. **流的交叉连接**:
   - `client_streams = (server_to_client_receive, client_to_server_send)`
   - `server_streams = (client_to_server_receive, server_to_client_send)`

   这确保客户端的发送流连接到服务器的接收流，反之亦然。

3. **任务组和生命周期管理**:
   - 服务器在单独的任务中运行
   - 使用 `anyio.create_task_group()` 管理任务生命周期
   - 确保在测试完成后服务器被正确关闭

### 会话初始化和配置

当你使用 `create_connected_server_and_client_session` 时，它会：

1. 创建内存流对
2. 在后台任务中启动服务器
3. 创建一个配置了适当回调的客户端会话
4. 调用 `client_session.initialize()` 执行完整的 MCP 初始化握手
5. 将初始化完成的客户端会话交给调用者使用
6. 当上下文退出时，取消服务器任务并清理资源

这个过程完全模拟了真实的 MCP 客户端-服务器交互，但全部在内存中进行。

## 使用场景和示例

### 1. 单元测试

最常见的用途是测试 MCP 服务器的功能，如测试用例所示：

```python
@pytest.mark.anyio
async def test_memory_server_and_client_connection(client_connected_to_server: ClientSession):
    # 使用预配置的客户端会话进行测试
    response = await client_connected_to_server.send_ping()
    assert isinstance(response, EmptyResult)
    
    # 测试资源列表
    resources = await client_connected_to_server.list_resources()
    assert len(resources.resources) == 1
    assert resources.resources[0].uri == "memory://test"
```

### 2. 服务器组件开发和测试

可以用于测试服务器侧功能，如工具、资源和提示：

```python
@pytest.mark.anyio
async def test_server_tool():
    server = Server(name="test_server")
    
    # 定义测试工具
    @server.call_tool()
    async def handle_call_tool(ctx, arguments):
        name = arguments.get("name", "World")
        return f"Hello, {name}!"
    
    # 使用内存连接测试
    async with create_connected_server_and_client_session(server) as client:
        result = await client.call_tool("handle_call_tool", {"name": "Test"})
        assert result == "Hello, Test!"
```

### 3. 客户端回调测试

测试客户端回调，如采样回调：

```python
@pytest.mark.anyio
async def test_sampling_callback():
    server = Server(name="test_server")
    
    # 实现一个记录采样请求的采样回调
    sampling_requests = []
    
    async def test_sampling(ctx, params):
        sampling_requests.append(params)
        return types.CreateMessageResult(
            role="assistant",
            content=types.TextContent(type="text", text="Generated text"),
            model="test-model",
            stopReason="endTurn",
        )
    
    # 添加测试工具，调用采样
    @server.call_tool()
    async def sampling_tool(ctx):
        result = await ctx.session.create_message(...)
        return f"Got: {result.content.text}"
    
    # 连接并测试
    async with create_connected_server_and_client_session(
        server, sampling_callback=test_sampling
    ) as client:
        await client.call_tool("sampling_tool", {})
        assert len(sampling_requests) == 1
```

## 与真实传输层的区别和优势

与真实传输层（如 HTTP、WebSocket 等）相比，内存传输有以下特点：

### 优势

1. **快速**: 消息直接在内存中传递，没有网络延迟
2. **可控**: 不依赖外部网络或系统
3. **简单**: 不需要配置服务器或端口
4. **隔离**: 每个测试都可以有自己独立的流，互不干扰
5. **直接**: 允许同一进程中的客户端和服务器组件交互

### 限制

1. **仅限进程内**: 只适用于同一 Python 进程内的通信
2. **不模拟网络特性**: 不能测试网络延迟、断线重连等场景
3. **不测试传输协议**: 绕过了真实传输协议的实现细节

## 技术实现要点

1. **异步设计**: 使用 `anyio` 的异步原语实现非阻塞 I/O
2. **上下文管理器**: 使用 `asynccontextmanager` 确保资源正确清理
3. **任务管理**: 利用 `anyio.create_task_group` 管理后台任务
4. **异常处理**: 支持通过流传递异常，维持错误传播链
5. **可配置性**: 支持各种会话参数和回调配置

## 总结

memory.py 是 MCP Python SDK 中的一个关键模块，专门用于在内存中创建客户端和服务器之间的通信通道。它主要用于测试和开发环境，使开发者能够快速验证 MCP 组件的功能，而无需配置真实的网络服务。

这个模块展示了异步 Python 编程的强大功能，以及 MCP SDK 灵活的架构设计，允许不同的传输实现（包括纯内存传输）共存并使用相同的会话抽象和协议实现。通过这种方式，开发者可以快速迭代开发流程，提高测试效率和质量，同时保持与真实场景的行为一致性。

zhkzly: 是 MCP Python SDK 中的一个关键模块，专门用于在内存中创建客户端和服务器之间的通信通道。它主要用于测试和开发环境，使开发者能够快速验证 MCP 组件的功能，而无需配置真实的网络服务。

进程间通信？？

GitHub Copilot: # MCP Python SDK 中的内存通信与进程间通信

你提出了一个很好的问题！我来澄清 MCP SDK 中的内存通信与真正的进程间通信(IPC)之间的区别。

## memory.py 不是用于进程间通信的

memory.py 模块创建的通信通道**不是**用于真正的进程间通信，而是:

1. **进程内通信**: 这些内存通道只在单个 Python 进程内工作，用于连接同一进程中的客户端和服务器组件
   
2. **测试和开发环境**: 主要用途是单元测试和集成测试，在不需要网络的环境中快速验证功能

3. **模拟传输层**: 它模拟了客户端和服务器之间的消息传递，但没有跨越进程边界

## 真正的进程间通信在 MCP SDK 中

MCP SDK 确实支持真正的进程间通信，但这是通过其他模块实现的:

1. **`stdio` 传输**: 使用标准输入/输出在不同进程间通信

   ```python
   # 在一个进程中运行服务器
   mcp = FastMCP("MyServer")
   mcp.run(transport="stdio")
   ```
   
   ```python
   # 在另一个进程中使用客户端连接
   server_params = StdioServerParameters(
       command="python", 
       args=["path/to/server_script.py"]
   )
   async with stdio_client(server_params) as (read, write):
       async with ClientSession(read, write) as session:
           # 进程间通信
           await session.initialize()
   ```

2. **`streamable_http` 传输**: 通过 HTTP 协议在不同进程甚至不同机器间通信

   ```python
   # 服务器进程
   mcp = FastMCP("MyServer")
   mcp.run(transport="streamable-http")
   ```
   
   ```python
   # 客户端进程
   async with streamablehttp_client("http://localhost:8000/mcp") as (read, write, _):
       async with ClientSession(read, write) as session:
           # 进程间甚至跨网络通信
           await session.initialize()
   ```

3. **`sse` 传输**: 通过 Server-Sent Events 协议在不同进程间通信

## 区别总结

| 特性 | memory.py (内存通信) | 真正的进程间通信 (stdio, HTTP) |
|------|----------------------|------------------------------|
| 作用域 | 单一 Python 进程内 | 跨不同进程，甚至跨网络 |
| 主要用途 | 测试、开发、快速验证 | 生产环境、实际应用场景 |
| 数据传递 | 直接内存引用，无序列化 | 通过字节流、网络协议，需序列化 |
| 启动方式 | 在同一代码中创建客户端和服务器 | 在不同进程中分别启动 |
| 资源开销 | 非常低 | 更高(包括进程间通信开销) |
| 错误情况 | 简单的异常传递 | 需要处理更复杂的错误场景(断连等) |

## 何时使用哪种方式

1. **使用内存通信(memory.py)**:
   - 单元测试和集成测试
   - 开发阶段快速验证组件功能
   - 不想处理进程管理和网络配置时

2. **使用真正的进程间通信**:
   - 实际应用场景
   - 测试与真实环境相同的通信模式
   - 需要模拟网络条件或测试断连重连

## 架构设计的优雅之处

MCP SDK 架构的优雅之处在于，无论使用内存通信还是实际的进程间通信，API 和行为模式保持一致:

```python
# 内存通信
async with create_connected_server_and_client_session(server) as session:
    await session.call_tool("my_tool", args)

# 进程间通信
async with streamablehttp_client("http://localhost:8000/mcp") as (read, write, _):
    async with ClientSession(read, write) as session:
        await session.call_tool("my_tool", args)
```

这种一致性使开发者可以在不改变代码结构的情况下，从测试环境过渡到实际部署环境。

总的来说，memory.py 是一个专门为测试设计的模块，提供了虚拟的通信通道，而不是真正的进程间通信解决方案。对于真正的进程间通信，MCP SDK 提供了多种传输实现，如 stdio、HTTP 和 SSE。

zhkzly: async def get_prompt 为什么要调用create_messages??

GitHub Copilot: # `get_prompt` 函数中调用 `create_messages` 的原因与作用

在 MCP 架构中，`get_prompt` 函数调用 `create_messages` 是实现提示功能的关键步骤。我来详细解释这个设计：

## 核心作用

`get_prompt` 函数是对 MCP 服务器的 `prompts/get` 请求的处理程序，它需要返回一个包含消息列表的 `GetPromptResult` 对象。而 `create_messages` 函数正是负责创建这些消息。

这种设计体现了职责分离的原则：

1. **`get_prompt`** - 处理请求参数，进行参数验证，并返回符合 MCP 协议的响应
2. **`create_messages`** - 专注于根据提供的参数构建适当的消息内容

## 工作流程详解

当 MCP 客户端发出 `prompts/get` 请求时：

1. 客户端提供提示名称和参数 (例如 `"simple"`, `{"context": "...", "topic": "..."}`)
2. 服务器接收请求并调用 `get_prompt` 处理程序
3. `get_prompt` 在此例中：
   - 验证提示名称 (`if name != "simple"...`)
   - 处理参数 (`if arguments is None...`)
   - 调用 `create_messages` 生成实际的提示消息列表
   - 将消息和描述封装在 `GetPromptResult` 中返回给客户端

## 为何分为两个函数

把消息创建逻辑分离到 `create_messages` 函数中有几个好处：

### 1. 关注点分离

- `get_prompt` 处理协议层面的请求/响应逻辑
- `create_messages` 专注于业务逻辑（构建提示内容）

### 2. 代码复用

如果需要在其他地方创建相同格式的消息，可以直接复用 `create_messages` 而不需要复制粘贴代码。

### 3. 更易于测试

可以单独测试 `create_messages` 函数，验证不同参数组合下生成的消息是否正确，而无需模拟整个 MCP 请求/响应周期。

### 4. 更好的可维护性

如果需要修改提示内容或格式，只需要修改 `create_messages` 函数，而不需要改动处理 MCP 协议的代码。

## 具体实现分析

在这个例子中：

```python
@app.get_prompt()
async def get_prompt(
    name: str, arguments: dict[str, str] | None = None
) -> types.GetPromptResult:
    if name != "simple":
        raise ValueError(f"Unknown prompt: {name}")

    if arguments is None:
        arguments = {}

    return types.GetPromptResult(
        messages=create_messages(
            context=arguments.get("context"), topic=arguments.get("topic")
        ),
        description="A simple prompt with optional context and topic arguments",
    )
```

`create_messages` 函数构建了一个消息列表，可能包含：
1. 可选的上下文消息 (如果提供了 `context` 参数)
2. 主要提示消息 (根据是否提供 `topic` 参数调整内容)

这种设计使得提示系统非常灵活，可以根据客户端提供的参数动态生成不同的提示内容。

## 总结

`get_prompt` 调用 `create_messages` 是一种良好的软件设计实践，体现了：

1. **关注点分离** - 协议处理与内容生成分离
2. **单一职责原则** - 每个函数专注于一个任务
3. **代码复用** - 消息创建逻辑可以在其他地方重用
4. **灵活性** - 可以根据不同参数动态调整提示内容

这种设计模式在 MCP 服务器的实现中很常见，有助于构建可维护、可测试和可扩展的 MCP 应用程序。

zhkzly: 我现在想要知道的是，一般而言是否是一个工具对应一个server还是多个工具对应于一个server？请基于当前的仓库进行回答，如果是一个工具对应一个server，那么client是如何发现这些server的？？它怎么知道其运行的ip 及端口？？

GitHub Copilot: # MCP工具和服务器的关系模式

在MCP Python SDK的设计中，关于工具与服务器的关系以及客户端发现服务器的方式，我可以基于当前仓库的代码结构和实现给你详细解答。

## 工具与服务器的关系模式

在MCP框架中，**多个工具通常对应于一个服务器**是最常见的模式。这在仓库中有充分的例证： 从这些示例可以看出，MCP框架的典型设计模式是：

### 1. 一个服务器，多个工具的模式

如echo.py示例所示，一个MCP服务器可以同时提供多种功能：
- 多个工具(`echo_tool`)
- 多个资源(`echo_resource`, `echo_template`)
- 多个提示(`echo_prompt`)

这是最常见的使用方式，这样设计的好处包括：
- 相关功能的逻辑聚合在一起
- 只需要部署和管理一个服务
- 客户端只需连接一个端点

### 2. 特殊情况：微服务架构

虽然不太常见，但MCP也支持微服务风格的架构，即"一个工具一个服务器"。这在仓库中有特定的示例，特别是在一些特殊工具需要隔离运行的情况下。

## 客户端如何发现和连接服务器

在MCP架构中，客户端发现和连接服务器的方式是**手动配置**的，而不是通过自动发现机制。这反映了MCP设计的一个关键理念：控制权在客户端手中。

### 客户端连接服务器的方式

客户端通常通过以下方式指定服务器信息： Summarized conversation historySummarizing conversation history...根据该仓库的代码和示例，我将详细回答关于工具与服务器的关系以及客户端如何发现服务器的问题。

## 工具与服务器的关系

在MCP (Model Context Protocol) Python SDK中，**一个服务器可以提供多个工具**。这是最常见的模式，而不是每个工具对应一个独立的服务器。

让我查看一些具体示例来证明这一点： 这个例子 echo.py 非常清晰地展示了一个服务器提供多个功能：
- 一个服务器实例 `mcp = FastMCP("Echo Server")` 
- 这个单一服务器实例提供了4种不同的功能：
  - 一个工具 `echo_tool`
  - 两个资源（一个静态资源和一个模板资源）
  - 一个提示模板 `echo_prompt`

让我再看一个更简单的例子： 这个例子虽然只实现了一个工具，但仍然遵循相同的模式：一个服务器实例 (`mcp`) 注册并提供了一个工具 (`echo`)。

让我们查看服务器的核心实现类来理解其设计： 

从导入语句中可以看到，`FastMCP` 类已经整合了多种功能管理器：
- `ToolManager` - 管理工具
- `ResourceManager` - 管理资源
- `PromptManager` - 管理提示模板

进一步查看 `FastMCP` 类的具体实现： 让我尝试搜索 FastMCP 类的初始化方法： 让我们看一下该文件更多内容： 

现在让我们在文件中找到 FastMCP 类的定义： 从这里我们可以看到 `FastMCP` 类的构造函数，它管理多个功能：
- `self._tool_manager = ToolManager(...)` - 管理工具
- `self._resource_manager = ResourceManager(...)` - 管理资源
- `self._prompt_manager = PromptManager(...)` - 管理提示模板

现在让我们看一下 `tool()` 装饰器的实现： 让我们查看 `tool()` 装饰器的具体实现： 

和 `resource()` 装饰器： 

Continue to iterate?
Copilot has been working on this problem for a while. It can continue to iterate, or you can send a new message to refine your prompt.

zhkzly: 默认的配置方式什么样子的？？一个服务器对应于多个工具的话，那么如果想要利用其它多个服务器的工具，那么如何做到呢？？我的客户端如何配置？？

GitHub Copilot: 我来详细解答你关于默认配置和客户端如何使用多个服务器工具的问题。

## 默认服务器配置

FastMCP服务器的默认配置可以从`Settings`类中看出，这里是默认配置的主要部分： 可以看到，默认情况下，FastMCP服务器：
- 监听本地地址 `127.0.0.1`
- 使用端口 `8000`
- 挂载在根路径 `/`
- 网络传输相关的路径有：
  - SSE (Server-Sent Events) 路径：`/sse`
  - 消息路径：`/messages/`
  - StreamableHTTP路径：`/mcp`

## 客户端如何使用多个服务器的工具

客户端想要利用多个服务器提供的工具，需要为每个服务器创建单独的会话（Session）。让我们查看客户端的示例代码： 

让我们查看一个简单的客户端实现，来了解客户端如何配置和连接到多个服务器： 

现在让我们看一下使用的配置文件： 现在让我们看一下客户端如何配置连接多个服务器： 

## 回答问题

基于以上代码分析，我来详细回答你的问题：

### 工具与服务器的关系

**一个服务器通常可以提供多个工具**。在MCP (Model Context Protocol)框架中，一个服务器通常会注册多个工具、资源和提示模板，提供给客户端使用。这是最常见的设计模式，通过一个服务器来集中管理相关功能。

像 `FastMCP` 类中专门有 `ToolManager`、`ResourceManager` 和 `PromptManager` 三个管理器来处理不同类型的功能。服务器通常使用装饰器 `@mcp.tool()`、`@mcp.resource()` 和 `@mcp.prompt()` 来注册这些功能。

### 客户端如何利用多个服务器的工具

要使用多个服务器提供的工具，客户端需要：

1. **单独配置每个服务器连接**：为每个服务器创建单独的会话（Session）
2. **获取每个服务器的工具列表**：连接后调用 `list_tools()` 方法
3. **调用特定服务器的工具**：根据需要执行对应服务器的工具

从 `simple-chatbot` 示例中，我们可以看到客户端通过以下方式进行配置：

1. **配置文件**：使用 `servers_config.json` 文件配置所有要连接的服务器
2. **创建多个服务器连接**：为每个配置创建一个 `Server` 实例
3. **初始化所有连接**：在会话开始时初始化所有服务器连接
4. **聚合工具列表**：从所有服务器获取工具列表并合并

配置文件示例（`servers_config.json`）：
```json
{
  "mcpServers": {
    "sqlite": {
      "command": "uvx",
      "args": ["mcp-server-sqlite", "--db-path", "./test.db"]
    },
    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-puppeteer"]
    }
  }
}
```

### 服务器发现机制（IP和端口）

客户端可以通过三种主要方式配置和发现服务器：

1. **直接进程通信（stdio）**：
   - 使用 `StdioServerParameters` 类配置本地命令执行
   - 客户端直接启动服务器进程并通过标准输入/输出进行通信
   - 无需配置IP/端口，因为是进程间直接通信

2. **HTTP通信（StreamableHTTP/SSE）**：
   - 明确指定服务器URL，如 `http://localhost:8000/mcp` 或 `http://localhost:8000/sse`
   - 默认配置是本地地址(`127.0.0.1`)和默认端口(通常是8000或3000)

3. **中央配置管理**：
   - 使用类似Claude Desktop的配置机制，在一个中央配置文件中管理所有服务器连接信息
   - 可以通过环境变量或配置文件来统一管理不同服务器的连接参数

在simple-chatbot示例中，客户端采用标准输入/输出(stdio)方式与服务器通信，无需配置IP和端口，而是直接运行命令启动服务器：

```python
server_params = StdioServerParameters(
    command=command,
    args=self.config["args"],
    env={**os.environ, **self.config["env"]}
    if self.config.get("env")
    else None,
)
stdio_transport = await self.exit_stack.enter_async_context(
    stdio_client(server_params)
)
read, write = stdio_transport
session = await self.exit_stack.enter_async_context(
    ClientSession(read, write)
)
await session.initialize()
```

如果需要使用HTTP通信，则需要提供服务器的URL：

```python
# StreamableHTTP方式
async with streamablehttp_client("http://localhost:8000/mcp") as (read_stream, write_stream, _):
    async with ClientSession(read_stream, write_stream) as session:
        # 使用session

# SSE方式
async with sse_client("http://localhost:8000/sse") as (read_stream, write_stream):
    async with ClientSession(read_stream, write_stream) as session:
        # 使用session
```

总结来说，MCP框架支持一个服务器提供多个工具，而客户端可以配置连接多个服务器并集成它们的所有工具。连接参数可以通过配置文件管理，支持直接进程通信或HTTP通信。

zhkzly: 请给我详细介绍FastMcp 这个类，包括其中的函数，变量，继承关系，使用方法。需要有代码示例，完全基于本仓库

GitHub Copilot: # FastMCP 类详解

FastMCP 是 MCP (Model Context Protocol) Python SDK 中的核心类，它提供了一个更符合人体工程学的接口来创建和管理 MCP 服务器。让我深入分析这个类的结构和功能。

## 类定义与继承关系

FastMCP 类位于 server.py 文件中。它没有直接继承自其他类，但内部组合了多个关键组件，包括：

- `MCPServer` - 核心的低级别服务器实现
- `ToolManager` - 管理工具的注册与访问
- `ResourceManager` - 管理资源的注册与访问
- `PromptManager` - 管理提示模板的注册与访问 

## 主要属性和内部变量

让我们看看 FastMCP 类的主要属性： FastMCP 类中的主要属性包括：

1. `settings`: Settings 类实例，包含服务器配置
2. `_mcp_server`: 核心低级别服务器实现
3. `_tool_manager`: 管理工具的注册与访问
4. `_resource_manager`: 管理资源的注册与访问
5. `_prompt_manager`: 管理提示模板的注册与访问
6. `_auth_server_provider`: 可选的 OAuth 授权服务器提供程序
7. `_event_store`: 可选的事件存储器，用于支持可恢复性
8. `_session_manager`: StreamableHTTP 会话管理器
9. `dependencies`: 服务器所需的依赖项列表

## 设置类 (Settings)

FastMCP 使用 `Settings` 类管理服务器配置。这个类基于 Pydantic 的 `BaseSettings`，支持从环境变量中加载配置： ## 主要方法

FastMCP 类提供了几个关键方法类别：

### 1. 装饰器方法

这些方法用于注册工具、资源和提示模板： ### 2. 传输和应用方法

这些方法用于创建不同类型的服务器应用和配置传输层： ### 3. 运行方法

这些方法用于启动服务器： ## 使用方法示例

下面是从仓库中的实际示例提取的 FastMCP 使用方法：

### 基本使用示例 

这是一个最简单的例子，创建了一个名为 "Echo Server" 的 FastMCP 服务器，并注册了一个名为 `echo` 的工具。

### 提供多种功能的示例 这个示例展示了如何创建包含各种功能的服务器：
1. 工具（`@mcp.tool()`）
2. 静态资源（`@mcp.resource("echo://static")`）
3. 模板资源（`@mcp.resource("echo://{text}")`）
4. 提示模板（`@mcp.prompt("echo")`）

### 使用上下文对象的高级工具示例 ## FastMCP 详细介绍

### 1. 类定义与概述

FastMCP 是 Model Context Protocol (MCP) Python SDK 中的一个核心类，提供了一个更符合人体工程学的接口来创建和管理 MCP 服务器。它位于 server.py 文件中，是对底层 MCP 服务器实现的高级包装。

FastMCP 类没有直接继承自其他类，但是内部使用了组合设计模式，组合了多个关键组件:

```python
from mcp.server.fastmcp import FastMCP

# 创建一个简单的 FastMCP 服务器
mcp = FastMCP("My Server", instructions="这是一个示例服务器")
```

### 2. 主要属性和内部组件

FastMCP 类中包含以下主要属性：

1. `settings`: Settings 类的实例，包含服务器的所有配置项
2. `_mcp_server`: 低级别的 MCPServer 实现
3. `_tool_manager`: 管理工具的注册和调用
4. `_resource_manager`: 管理资源的注册和访问
5. `_prompt_manager`: 管理提示模板
6. `_auth_server_provider`: 可选的 OAuth 授权服务器提供程序
7. `_event_store`: 可选的事件存储器（用于支持会话恢复）
8. `_session_manager`: StreamableHTTP 会话管理器
9. `dependencies`: 服务器所需的依赖项列表

### 3. 构造函数

FastMCP 的构造函数支持多种参数，可以自定义服务器的名称、说明和行为：

```python
def __init__(
    self,
    name: str | None = None,  # 服务器名称
    instructions: str | None = None,  # 服务器说明
    auth_server_provider: OAuthAuthorizationServerProvider[Any, Any, Any] | None = None,  # OAuth提供程序
    event_store: EventStore | None = None,  # 事件存储器
    *,
    tools: list[Tool] | None = None,  # 初始工具列表
    **settings: Any,  # 服务器设置
):
```

基本用法：

```python
from mcp.server.fastmcp import FastMCP

# 创建基本服务器
mcp = FastMCP("我的服务器")

# 创建带说明的服务器
mcp = FastMCP("我的服务器", instructions="这个服务器提供数据分析功能")

# 创建带依赖项的服务器
mcp = FastMCP("分析服务器", dependencies=["pandas", "numpy", "scikit-learn"])
```

### 4. Settings 类

FastMCP 使用 Pydantic 的 BaseSettings 来管理配置，支持从环境变量加载设置：

```python
class Settings(BaseSettings, Generic[LifespanResultT]):
    """FastMCP server settings.
    All settings can be configured via environment variables with the prefix FASTMCP_.
    For example, FASTMCP_DEBUG=true will set debug=True.
    """

    model_config = SettingsConfigDict(
        env_prefix="FASTMCP_",
        env_file=".env",
        env_nested_delimiter="__",
        nested_model_default_partial_update=True,
        extra="ignore",
    )

    # 服务器设置
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # HTTP设置
    host: str = "127.0.0.1"
    port: int = 8000
    mount_path: str = "/"
    sse_path: str = "/sse"
    message_path: str = "/messages/"
    streamable_http_path: str = "/mcp"
    
    # ... 更多设置 ...
```

### 5. 主要方法和功能

#### 5.1 工具管理

FastMCP 提供了注册和管理工具的功能：

```python
# 使用装饰器注册工具
@mcp.tool()
def calculate(x: int, y: int) -> int:
    """计算两个数字的和"""
    return x + y

# 或直接添加工具
def multiply(x: int, y: int) -> int:
    """计算两个数字的乘积"""
    return x * y

mcp.add_tool(multiply)
```

带有上下文的工具示例：

```python
# 使用Context对象访问MCP功能
@mcp.tool()
async def process_with_progress(data: list[str], ctx: Context) -> str:
    """处理数据并报告进度"""
    total = len(data)
    
    for i, item in enumerate(data):
        # 记录处理状态
        await ctx.info(f"处理项目 {item}")
        
        # 报告进度
        await ctx.report_progress(i, total, f"已完成 {i}/{total}")
        
    return f"成功处理 {total} 个项目"
```

#### 5.2 资源管理

资源是可以被客户端读取的数据：

```python
# 静态资源
@mcp.resource("data://static/info")
def get_static_info() -> str:
    return "这是一些静态信息"

# 动态资源 (模板资源)
@mcp.resource("data://user/{user_id}")
def get_user_data(user_id: str) -> str:
    return f"用户 {user_id} 的数据"
```

#### 5.3 提示模板管理

提示模板是预定义的 LLM 提示：

```python
@mcp.prompt()
def analyze_data(topic: str) -> str:
    return f"请分析关于 {topic} 的数据并提供见解"

# 多消息提示
@mcp.prompt()
def complex_prompt(query: str, context: str = "general") -> list[dict]:
    return [
        {"role": "system", "content": f"上下文: {context}"},
        {"role": "user", "content": query}
    ]
```

#### 5.4 运行服务器

FastMCP 支持多种传输方式运行服务器：

```python
# 使用标准输入/输出
mcp.run(transport="stdio")

# 使用 SSE 传输
mcp.run(transport="sse")

# 使用 Streamable HTTP
mcp.run(transport="streamable-http")
```

#### 5.5 上下文对象 (Context)

Context 对象提供了在工具和资源函数中访问 MCP 功能的接口：

```python
@mcp.tool()
async def tool_with_context(query: str, ctx: Context) -> str:
    # 日志记录
    await ctx.debug("调试消息")
    await ctx.info(f"处理查询: {query}")
    await ctx.warning("这是一个警告")
    
    # 进度报告
    await ctx.report_progress(0.5, 1.0, "处理中...")
    
    # 读取资源
    resource_data = await ctx.read_resource("resource://some-data")
    
    # 请求信息
    request_id = ctx.request_id
    
    return f"处理完成: {query}"
```

#### 5.6 图片处理

FastMCP 提供了 Image 类来简化图片处理：

```python
from mcp.server.fastmcp import FastMCP, Image
from PIL import Image as PILImage

mcp = FastMCP("图片处理服务")

@mcp.tool()
def create_thumbnail(image_path: str) -> Image:
    """创建图片缩略图"""
    img = PILImage.open(image_path)
    img.thumbnail((100, 100))
    
    # 将PIL图像转换为MCP Image
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    return Image(data=buffer.getvalue(), format="jpeg")
```

### 6. 生命周期管理

FastMCP 支持通过 lifespan 函数管理服务器的生命周期：

```python
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass

@dataclass
class AppContext:
    db: Database

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """管理应用生命周期，提供类型安全的上下文"""
    # 启动时初始化
    db = await Database.connect()
    try:
        yield AppContext(db=db)
    finally:
        # 关闭时清理
        await db.disconnect()

# 将lifespan函数传递给服务器
mcp = FastMCP("我的应用", lifespan=app_lifespan)
```

### 7. 综合示例

以下是一个综合示例，展示了 FastMCP 的多种功能：

```python
"""
FastMCP 综合示例：文本分析服务器
"""

import httpx
from mcp.server.fastmcp import FastMCP, Context, Image
import io
from PIL import Image as PILImage
import matplotlib.pyplot as plt
import numpy as np

# 创建服务器，并指定依赖项
mcp = FastMCP(
    "文本分析服务", 
    instructions="提供文本分析和可视化工具",
    dependencies=["matplotlib", "numpy", "nltk", "pillow"]
)

# 工具 - 简单文本分析
@mcp.tool()
def word_count(text: str) -> dict:
    """计算文本中的字数统计"""
    words = text.split()
    return {
        "total_words": len(words),
        "unique_words": len(set(words)),
        "average_word_length": sum(len(word) for word in words) / len(words) if words else 0
    }

# 工具 - 带进度报告的异步工具
@mcp.tool()
async def sentiment_analysis(text: str, ctx: Context) -> str:
    """分析文本情感"""
    import nltk
    
    # 确保必要的NLTK数据已下载
    try:
        nltk.data.find('vader_lexicon')
    except LookupError:
        await ctx.info("下载NLTK数据...")
        nltk.download('vader_lexicon')
        
    from nltk.sentiment import SentimentIntensityAnalyzer
    
    # 报告进度
    await ctx.report_progress(0.3, 1.0, "初始化分析器...")
    
    # 记录信息
    await ctx.info(f"分析文本: {text[:50]}...")
    
    # 执行分析
    analyzer = SentimentIntensityAnalyzer()
    scores = analyzer.polarity_scores(text)
    
    await ctx.report_progress(0.8, 1.0, "分析完成")
    
    # 确定情感
    compound = scores['compound']
    if compound >= 0.05:
        sentiment = "积极"
    elif compound <= -0.05:
        sentiment = "消极"
    else:
        sentiment = "中性"
    
    await ctx.report_progress(1.0, 1.0, "完成")
    
    return f"情感分析结果: {sentiment} (复合分数: {compound:.2f})"

# 工具 - 返回图像
@mcp.tool()
def create_word_length_chart(text: str) -> Image:
    """创建单词长度的分布图"""
    words = text.split()
    lengths = [len(word) for word in words]
    
    # 绘制分布图
    plt.figure(figsize=(10, 6))
    plt.hist(lengths, bins=range(1, 21), alpha=0.7)
    plt.xlabel('单词长度')
    plt.ylabel('频率')
    plt.title('单词长度分布')
    plt.grid(True, alpha=0.3)
    
    # 将图像保存到内存
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    plt.close()
    
    return Image(data=buffer.getvalue(), format="png")

# 资源 - 静态文本
@mcp.resource("text://example")
def example_text() -> str:
    return """这是一段示例文本，用于演示文本分析功能。
    这段文本包含多个句子和不同长度的单词，可以用来测试分析工具。
    文本分析可以帮助我们了解文本的基本特征，如字数、词频和情感倾向等。"""

# 资源 - 动态模板
@mcp.resource("text://sample/{language}")
def sample_text(language: str) -> str:
    samples = {
        "chinese": "这是一段中文示例文本，用于测试文本分析工具。",
        "english": "This is a sample English text for testing text analysis tools.",
        "spanish": "Este es un texto de ejemplo en español para probar herramientas de análisis de texto."
    }
    return samples.get(language.lower(), f"不支持的语言: {language}")

# 提示模板
@mcp.prompt()
def analyze_document(document: str) -> str:
    return f"""请分析以下文档，并提供其主题、关键点和写作风格的摘要：

文档内容:
{document}

请提供:
1. 文档主题
2. 关键点列表
3. 写作风格评估
"""
```

如果要运行这个服务器：

```python
if __name__ == "__main__":
    # 使用标准输入/输出运行服务器
    mcp.run(transport="stdio")
    
    # 或使用HTTP运行服务器
    # mcp.run(transport="streamable-http")
```

### 8. FastMCP 的特点和优势

1. **简化的工具和资源管理** - 使用装饰器和直观的API简化了工具和资源的注册
2. **类型安全** - 使用 Python 类型注解确保接口的一致性和正确性
3. **多种传输协议支持** - 支持 stdio、SSE 和 Streamable HTTP
4. **灵活的配置** - 支持从环境变量和配置文件加载设置
5. **内置上下文对象** - 提供了 Context 对象以访问 MCP 功能
6. **图像处理支持** - 内置 Image 类简化了图像处理
7. **生命周期管理** - 强大的生命周期管理功能
8. **多种运行模式** - 支持开发模式、部署模式和 Claude Desktop 集成

### 9. 总结

FastMCP 类是 MCP Python SDK 中的核心组件，提供了一个高级接口来创建和管理 Model Context Protocol 服务器。它支持工具、资源和提示模板的注册和管理，并提供了上下文对象以访问各种 MCP 功能。通过 FastMCP，开发人员可以轻松创建与 LLM 应用程序集成的服务器，同时获得类型安全、灵活的配置和多种传输选项的好处。

FastMCP 的设计遵循组合模式，它组合了多个专门的管理器类来处理不同类型的功能，包括工具管理器、资源管理器和提示管理器。这种设计使代码更易于理解和维护，也使 FastMCP 能够提供丰富的功能集。

zhkzly: Context 对象提供了在工具和资源函数中访问 MCP 功能的接口：
async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any],
        context: Context[ServerSessionT, LifespanContextT] | None = None,
    ) -> Any:
        """Call a tool by name with arguments."""
        tool = self.get_tool(name)
        if not tool:
            raise ToolError(f"Unknown tool: {name}")

        return await tool.run(arguments, context=context)


上述工具调用的时候，context这个里面到底有什么函数，变量？？？是包含所有的对话历史还是根据 客户端的指定？？

GitHub Copilot: # Context 对象的详细内容和功能

在 FastMCP 中，`Context` 对象是一个非常重要的组件，它为工具和资源函数提供了访问 MCP 功能的接口。我将详细解释 Context 对象的内容、功能和用途。

## Context 对象的定义

Context 对象定义在 server.py 文件中。让我们先查看它的定义： ## Context 对象的属性和方法

让我们继续查看 Context 对象的属性和方法： ## Context 对象的详细解释

从上面的代码中，我们可以看到 Context 对象主要包含以下内容：

### 1. 核心属性

1. `_request_context`: 底层的 RequestContext 对象，包含请求的详细信息
2. `_fastmcp`: 所属的 FastMCP 服务器实例

### 2. 主要方法和属性

#### 日志记录方法
- `async def debug(message: str, **extra)`: 发送调试级别的日志消息
- `async def info(message: str, **extra)`: 发送信息级别的日志消息
- `async def warning(message: str, **extra)`: 发送警告级别的日志消息
- `async def error(message: str, **extra)`: 发送错误级别的日志消息
- `async def log(level, message, logger_name=None)`: 发送指定级别的日志消息

#### 进度报告
- `async def report_progress(progress: float, total: float = None, message: str = None)`: 报告当前操作的进度

#### 资源访问
- `async def read_resource(uri: str | AnyUrl)`: 读取指定 URI 的资源内容

#### 请求信息
- `@property def request_id() -> str`: 获取当前请求的唯一 ID
- `@property def client_id() -> str | None`: 获取客户端 ID（如果可用）

#### 高级访问
- `@property def session()`: 访问底层会话对象，用于高级用例
- `@property def fastmcp() -> FastMCP`: 访问 FastMCP 服务器实例
- `@property def request_context()`: 访问底层请求上下文

## Context 对象的使用场景

让我们看一下在 FastMCP 的代码库中是如何使用 Context 对象的。首先，我们看一下具体的使用示例： Summarized conversation historySummarizing conversation history...I'll help you understand what the `Context` object contains in the FastMCP framework and what capabilities it provides during tool invocation.

Let me examine the relevant code to give you a detailed explanation of the `Context` object. Let me continue reading the file to find the `Context` class definition: Let me examine the main `Context` class definition in the FastMCP framework: Let me read the rest of the Context class: Let me also check out what's in the `lifespan_context` that may be available in the Context: Let me look at how the `Context` object is used in a tool implementation: 

Let's examine a more advanced example where the Context is used: 

Let me check the memory.py example which has more advanced Context usage: Let me check one of the examples that actually uses the Context: 

Let me check some FastMCP examples showing how Context is used in practice: 

Continue to iterate?
Copilot has been working on this problem for a while. It can continue to iterate, or you can send a new message to refine your prompt.

zhkzly: 据我了解，mcp server 似乎可以自己定义，也可以在开源社区下载，每个下载的内容都包含多个mcp server,客户端如何知道怎么配置的？？

GitHub Copilot: MCP（Model Context Protocol）服务器确实可以自己定义或从开源社区获取，而且一个代码库中可能包含多个MCP服务器实现。关于客户端如何知道如何配置这些服务器，我来解释一下这个过程。

## MCP 客户端与服务器配置

在MCP协议中，客户端需要知道如何连接到服务器以及服务器提供了哪些功能。这个配置过程有几种方式：

### 1. 传输协议发现

MCP支持几种主要的传输协议：
- STDIO（标准输入/输出）
- SSE（Server-Sent Events）
- Streamable HTTP

客户端需要知道服务器使用的是哪种传输协议，以及任何相关的连接参数（如HTTP服务器的地址和端口）。

### 2. 初始化过程

当客户端连接到MCP服务器时，会进行初始化过程，包括：

1. **初始化请求**：客户端发送`initialize`请求，包含客户端信息和支持的功能
2. **初始化响应**：服务器回复支持的功能列表
3. **初始化通知**：客户端发送`initialized`通知，确认初始化完成

这个过程让客户端了解服务器提供的能力。

### 3. 工具和资源发现

初始化后，客户端可以：
- 调用`list_tools`获取服务器提供的工具列表
- 调用`list_resources`获取服务器提供的资源列表
- 调用`list_prompts`获取服务器提供的提示模板列表

这样客户端就能动态发现服务器的功能，而不需要硬编码。

### 4. 配置文件和环境变量

实际使用中，MCP服务器和客户端的配置通常通过以下方式指定：

1. **配置文件**：例如JSON或YAML格式的配置文件
2. **环境变量**：通过环境变量设置连接参数
3. **命令行参数**：启动时通过命令行指定参数

### 实际案例

在您提供的代码中，以`simple-chatbot`客户端为例，客户端配置是这样处理的：

```python
# 配置服务器列表
servers = [
    {
        "name": "server1",
        "command": "npx",
        "args": ["claude-mcp-server"],
        "env": {"CLAUDE_API_KEY": os.environ.get("CLAUDE_API_KEY")}
    },
    {
        "name": "server2", 
        "command": "uv",
        "args": ["run", "mcp-simple-tool"],
        "env": {}
    }
]

# 初始化服务器连接
async def initialize(self) -> None:
    command = shutil.which("npx") if self.config["command"] == "npx" else self.config["command"]
    
    server_params = StdioServerParameters(
        command=command,
        args=self.config["args"],
        env={**os.environ, **self.config["env"]}
    )
    
    # 创建连接
    stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
    read, write = stdio_transport
    session = await self.exit_stack.enter_async_context(ClientSession(read, write))
    await session.initialize()  # 发送初始化请求
    self.session = session
```

客户端连接到服务器后，通过标准的MCP协议方法来发现和使用服务器的功能：

```python
# 列出服务器提供的工具
async def list_tools(self) -> list[Any]:
    if not self.session:
        await self.initialize()
    result = await self.session.list_tools()
    return [
        Tool(
            name=tool.name,
            description=tool.description or "",
            input_schema=tool.inputSchema,
        )
        for tool in result.tools
    ]

# 执行工具
async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
    if not self.session:
        await self.initialize()
    return await self.session.call_tool(tool_name, arguments)
```

## 总结

MCP客户端配置服务器的流程是：

1. **指定连接参数**：通过配置文件、环境变量或命令行参数指定如何连接到服务器
2. **建立连接**：使用指定的传输协议（STDIO、SSE或Streamable HTTP）连接到服务器
3. **初始化**：通过MCP协议的初始化过程交换能力信息
4. **发现功能**：调用标准接口发现服务器提供的工具、资源和提示模板
5. **使用功能**：基于发现的信息调用相应的工具和资源

这种动态发现的方式使得客户端可以适应不同的MCP服务器实现，而不需要为每个服务器编写特定的代码。

zhkzly: # 配置服务器列表
servers = [
    {
        "name": "server1",
        "command": "npx",
        "args": ["claude-mcp-server"],
        "env": {"CLAUDE_API_KEY": os.environ.get("CLAUDE_API_KEY")}
    },
    {
        "name": "server2", 
        "command": "uv",
        "args": ["run", "mcp-simple-tool"],
        "env": {}
    }
]

仅仅是这样子配置，client怎么知道端口在哪里？？

GitHub Copilot: 您提出了一个很好的问题。在您展示的配置中，确实没有明确指定端口信息，这是因为这个配置使用的是STDIO（标准输入/输出）传输协议，而不是基于网络的HTTP或SSE传输。

## STDIO传输协议不需要端口

在这个配置中：

```python
servers = [
    {
        "name": "server1",
        "command": "npx",
        "args": ["claude-mcp-server"],
        "env": {"CLAUDE_API_KEY": os.environ.get("CLAUDE_API_KEY")}
    },
    {
        "name": "server2", 
        "command": "uv",
        "args": ["run", "mcp-simple-tool"],
        "env": {}
    }
]
```

客户端使用的是STDIO传输协议，通过以下方式工作：

1. 客户端**启动一个子进程**来运行MCP服务器
2. 客户端通过**子进程的标准输入/输出**进行通信
3. 不需要TCP/IP端口，因为通信是通过进程间的stdin/stdout流完成的

这就是为什么配置中有`"command"`和`"args"`字段，而不是主机和端口信息。

## STDIO连接流程

当使用此配置时，MCP客户端会：

1. 执行命令（如`npx claude-mcp-server`或`uv run mcp-simple-tool`）
2. 创建一个子进程
3. 通过子进程的stdin/stdout与服务器交换MCP协议消息

代码中的这部分实现了这个过程：

```python
server_params = StdioServerParameters(
    command=command,
    args=self.config["args"],
    env={**os.environ, **self.config["env"]}
)

stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
read, write = stdio_transport
```

## 如果使用HTTP/SSE传输

如果要使用基于网络的传输协议（如HTTP或SSE），配置会不同，需要包含主机和端口信息：

```python
servers = [
    {
        "name": "http-server",
        "transport": "streamable-http",
        "url": "http://localhost:3000/mcp",  # 这里指定了主机和端口
        "env": {}
    },
    {
        "name": "sse-server",
        "transport": "sse",
        "url": "http://localhost:8000/sse",  # 这里指定了主机和端口
        "env": {}
    }
]
```

## MCP传输协议的类型

MCP支持三种主要的传输协议：

1. **STDIO**：
   - 优点：简单，无需网络配置
   - 缺点：只能在本地使用，无法远程访问

2. **SSE（Server-Sent Events）**：
   - 优点：基于HTTP，可以远程访问
   - 缺点：需要配置网络（主机、端口）

3. **Streamable HTTP**：
   - 优点：也是基于HTTP，支持更高效的流式传输
   - 缺点：同样需要网络配置

您展示的配置使用的是第一种（STDIO），这也是为什么没有端口信息的原因。

## 总结

- **STDIO传输**（您展示的配置）通过子进程的标准输入/输出通信，不需要端口
- 子进程是通过执行`"command"`和`"args"`指定的命令创建的
- 如果要使用HTTP或SSE传输，则需要在配置中指定URL，包含主机和端口

这种设计使得MCP协议非常灵活，可以在不同的通信场景下使用。

zhkzly: STDIO：

优点：简单，无需网络配置
缺点：只能在本地使用，无法远程访问

这个进程间通信是如何实现的？如何实现跨进程调用函数？如果client 采用list_tools那么是所有的server都返回tools？？还是说需要client指定？？

GitHub Copilot: 您提出了几个关于STDIO传输机制以及MCP客户端与服务器交互的重要问题。我将详细解释这些问题。

## STDIO进程间通信的实现

STDIO（标准输入/输出）进程间通信在MCP中的实现依赖于以下机制：

### 1. 进程创建和管道

当客户端使用STDIO传输时，它会创建一个子进程来运行MCP服务器，并建立与子进程的双向通信通道：

```python
# 简化版的实现逻辑
async def stdio_client(server_params: StdioServerParameters) -> Tuple[StreamReader, StreamWriter]:
    # 创建子进程
    process = await asyncio.create_subprocess_exec(
        server_params.command,
        *server_params.args,
        stdin=asyncio.subprocess.PIPE,  # 为子进程提供标准输入管道
        stdout=asyncio.subprocess.PIPE,  # 捕获子进程的标准输出
        env=server_params.env
    )
    
    # 创建读写流
    reader = StreamReader(process.stdout)  # 从子进程的标准输出读取
    writer = StreamWriter(process.stdin)   # 写入到子进程的标准输入
    
    return reader, writer
```

### 2. JSON-RPC 协议

MCP使用JSON-RPC协议格式化消息，使进程间通信更加结构化：

```
// 发送到服务器的请求示例
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}

// 从服务器接收的响应示例
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {
        "name": "echo",
        "description": "Echo the input text",
        "inputSchema": {...}
      }
    ]
  }
}
```

消息通过进程的标准输入/输出流传递，每个消息由换行符分隔。

### 3. 异步I/O处理

MCP使用异步I/O（通过`asyncio`或`anyio`）来处理读写操作，避免阻塞：

```python
async def send_message(writer, message):
    # 序列化消息为JSON
    json_data = json.dumps(message)
    # 写入数据到子进程的标准输入
    await writer.write(f"{json_data}\n")
    
async def receive_message(reader):
    # 从子进程的标准输出读取一行数据
    line = await reader.readline()
    # 解析JSON消息
    return json.loads(line)
```

## 跨进程函数调用的实现

MCP不是直接进行跨进程函数调用，而是使用一种基于消息的协议模式：

### 1. 远程过程调用 (RPC) 模式

客户端通过发送JSON-RPC消息来"调用"服务器上的功能：

```python
# 客户端代码
async def call_tool(self, tool_name, arguments):
    # 构建JSON-RPC请求
    request = {
        "jsonrpc": "2.0",
        "id": self._next_id(),
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }
    
    # 发送请求并等待响应
    result = await self._send_request(request)
    return result
```

### 2. 函数映射

服务器端会将这些RPC请求映射到实际的Python函数：

```python
# 服务器代码
@server.call_tool()
async def handle_tool_call(name, arguments):
    tool = find_tool_by_name(name)
    if tool:
        # 执行实际函数
        return await tool.run(arguments)
    else:
        raise Error("Tool not found")
```

## 多服务器场景下的工具调用

关于您的问题"如果client采用list_tools那么是所有的server都返回tools？还是说需要client指定？"：

### 客户端需要指定服务器

在多服务器配置中，客户端需要明确指定要与哪个服务器通信：

```python
# 客户端代码示例
async def list_all_tools(self):
    all_tools = []
    
    # 对每个配置的服务器
    for server_config in self.servers:
        server = Server(server_config["name"], server_config)
        await server.initialize()
        
        # 获取此服务器的工具
        server_tools = await server.list_tools()
        all_tools.extend(server_tools)
    
    return all_tools
```

在现实场景中，客户端通常会建立与每个服务器的单独连接，并根据需要与特定服务器交互。例如，在您之前提供的`simple-chatbot`的代码中：

```python
# 初始化特定服务器
server = Server(server_name, server_config)
await server.initialize()

# 列出该服务器的工具
tools = await server.list_tools()

# 在特定服务器上执行工具
result = await server.execute_tool(tool_name, arguments)
```

简单来说：

1. 客户端需要明确指定与哪个服务器通信
2. 每个`list_tools`调用只会返回单个服务器的工具列表
3. 如果客户端想要获得所有服务器的工具，需要分别查询每个服务器并合并结果

这种设计允许客户端根据需要从多个专门的MCP服务器获取功能，并将它们组合起来提供更丰富的能力。