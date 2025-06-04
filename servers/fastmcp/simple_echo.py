"""
FastMCP Echo Server
"""

from mcp.server.fastmcp import FastMCP

# Create server
mcp = FastMCP("Echo Server")


@mcp.tool()
def echo(text: str) -> str:
    """Echo the input text"""
    return text

def main():
    """Run the MCP server"""
    mcp.run()

if __name__ == "__main__":
    main()