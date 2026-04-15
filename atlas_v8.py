"""atlas_v8.py — MCP client with dynamic tool discovery and multi-server composition.

Connects to MCP servers, discovers available tools at runtime, converts them
to Anthropic tool format, and routes tool calls back to the correct server.

Requires: ANTHROPIC_API_KEY environment variable.
Requires: Node.js (for npx-based MCP servers) or Python MCP servers.
Usage: python atlas_v8.py
"""

import os
import sys
import json
import asyncio
import anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# ============================================================================
# MCP Server Configuration
# ============================================================================

MCP_SERVERS = {
    "filesystem": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", os.getcwd()],
    },
    "weather": {
        "command": sys.executable,
        "args": ["weather_server.py"],
    },
}

MODEL = "claude-sonnet-4-6"
SYSTEM_PROMPT = (
    "You are Atlas, an AI assistant with access to tools discovered from MCP servers. "
    "Use the available tools to help the user. Explain what you're doing."
)


# ============================================================================
# Tool Discovery
# ============================================================================

async def discover_all_tools(server_configs: dict) -> dict:
    """Connect to each MCP server and collect discovered tools."""
    all_tools = {}
    for name, cfg in server_configs.items():
        params = StdioServerParameters(
            command=cfg["command"],
            args=cfg.get("args", []),
            env=cfg.get("env"),
        )
        try:
            async with stdio_client(params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    result = await session.list_tools()
                    all_tools[name] = result.tools
                    print(f"[{name}] Discovered {len(result.tools)} tools")
                    for tool in result.tools:
                        print(f"  - {tool.name}: {tool.description[:60]}...")
        except Exception as e:
            print(f"[{name}] Failed to connect: {e}")
    return all_tools


# ============================================================================
# Tool Format Conversion
# ============================================================================

def mcp_tools_to_anthropic(all_tools: dict) -> list[dict]:
    """Convert MCP tool metadata to Anthropic tool definitions."""
    anthropic_tools = []
    for server_name, tools in all_tools.items():
        for tool in tools:
            anthropic_tools.append({
                "name": f"{server_name}__{tool.name}",
                "description": f"[{server_name}] {tool.description}",
                "input_schema": tool.inputSchema,
            })
    return anthropic_tools


def parse_tool_call(prefixed_name: str) -> tuple[str, str]:
    """Split 'filesystem__read_text_file' into ('filesystem', 'read_text_file')."""
    server_name, _, tool_name = prefixed_name.partition("__")
    return server_name, tool_name


# ============================================================================
# Tool Execution via MCP
# ============================================================================

async def execute_mcp_tool(server_config: dict, tool_name: str, arguments: dict) -> str:
    """Connect to an MCP server and execute a single tool call."""
    params = StdioServerParameters(
        command=server_config["command"],
        args=server_config.get("args", []),
        env=server_config.get("env"),
    )
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            return result.content[0].text if result.content else "(no output)"


# ============================================================================
# Agent Loop with MCP Tools
# ============================================================================

async def chat(user_message: str, server_configs: dict):
    """Run a tool-use exchange using MCP-discovered tools."""
    client = anthropic.Anthropic()

    # Discover tools from all configured servers
    all_tools = await discover_all_tools(server_configs)
    anthropic_tools = mcp_tools_to_anthropic(all_tools)

    if not anthropic_tools:
        print("No tools discovered. Check your MCP server configuration.")
        return

    messages = [{"role": "user", "content": user_message}]

    response = client.messages.create(
        model=MODEL, max_tokens=4096,
        system=SYSTEM_PROMPT, tools=anthropic_tools, messages=messages,
    )

    # Loop to handle multiple rounds of tool use
    while response.stop_reason == "tool_use":
        for block in response.content:
            if block.type == "text" and block.text.strip():
                print(f"Atlas: {block.text}\n")

        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            server_name, tool_name = parse_tool_call(block.name)
            print(f"  [MCP] Calling {server_name}/{tool_name}")

            if server_name not in server_configs:
                result = f"Error: unknown server '{server_name}'"
            else:
                try:
                    result = await execute_mcp_tool(
                        server_configs[server_name], tool_name, block.input
                    )
                except Exception as e:
                    result = f"Error: {type(e).__name__}: {e}"

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result,
            })

        messages.append({"role": "user", "content": tool_results})

        response = client.messages.create(
            model=MODEL, max_tokens=4096,
            system=SYSTEM_PROMPT, tools=anthropic_tools, messages=messages,
        )

    # Print final response
    for block in response.content:
        if block.type == "text":
            print(f"Atlas: {block.text}\n")


# ============================================================================
# Main
# ============================================================================

def main():
    print("Atlas v8 — MCP-Connected Assistant\n")

    prompt = "List the Python files in the current directory, find the largest one, and summarize what it does."
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])

    print(f"User: {prompt}\n")
    asyncio.run(chat(prompt, MCP_SERVERS))


if __name__ == "__main__":
    main()
