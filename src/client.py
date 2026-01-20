import sys
import json
import logging
import shutil
from typing import Any
from pathlib import Path
from contextlib import AsyncExitStack

from mcp.types import Tool as MCPTool
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters

from pydantic_ai.tools import ToolDefinition
from pydantic_ai import RunContext, Tool as PydanticTool
from mcp.types import LoggingMessageNotificationParams

# Configure logging
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


async def logging_callback(params: LoggingMessageNotificationParams):
    print(params.data)


async def print_progress_callback(
    progress: float, total: float | None, message: str | None
):
    if total is not None:
        percentage = (progress / total) * 100
        print(f"Progress: {progress}/{total} ({percentage:.1f}%)")
    else:
        print(f"Progress: {progress}")


class MCPClient:
    def __init__(self, config_path: str) -> None:
        self.config_path = Path(config_path)
        self.exit_stack = AsyncExitStack()
        self.sessions: dict[str, ClientSession] = {}
        self.list_tools: list[PydanticTool] = []
        self.list_prompts = []
        self.list_resources = []

    async def connect_to_server(self, server_name: str, server_config: dict) -> None:
        """Connect to a single MCP server."""
        try:
            command = (
                shutil.which("npx")
                if server_config["command"] == "npx"
                else server_config["command"]
            )
            server_params = StdioServerParameters(
                command=command,
                args=server_config["args"],
                cwd=server_config.get("cwd", None),
            )
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            read, write = stdio_transport
            session = await self.exit_stack.enter_async_context(
                ClientSession(read, write, logging_callback=logging_callback)
            )
            await session.initialize()

            try:
                # List available tools for this session
                tools_response = await session.list_tools()
                logging.info(
                    f"Connected to {server_name} with tools: {[t.name for t in tools_response.tools]}."
                )

                for tool in tools_response.tools:
                    self.sessions[tool.name] = session
                    self.list_tools.append(self._create_pydantic_tool_instance(tool))

                # List available prompts
                prompts_response = await session.list_prompts()
                if prompts_response and prompts_response.prompts:
                    for prompt in prompts_response.prompts:
                        self.sessions[prompt.name] = session
                        self.list_prompts.append(
                            {
                                "name": prompt.name,
                                "description": prompt.description,
                                "arguments": prompt.arguments,
                            }
                        )

                # List available resources
                resources_response = await session.list_resources()
                if resources_response and resources_response.resources:
                    for resource in resources_response.resources:
                        resource_uri = str(resource.uri)
                        self.sessions[resource_uri] = session
                        self.list_resources.append(resource_uri)
            except Exception as e:
                logging.error(f"Error {e}")

        except Exception as e:
            logging.error(f"Failed to connect to {server_name}: {e}")

    async def connect_to_servers(self) -> None:
        """Connect to all configured MCP servers."""
        try:
            with self.config_path.open(mode="r", encoding="utf-8") as file:
                data = json.load(file)
            servers = data.get("mcpServers", {})
            for server_name, server_config in servers.items():
                await self.connect_to_server(server_name, server_config)
        except Exception as e:
            logging.error(f"Error loading server configuration: {e}")
            raise

    def _create_pydantic_tool_instance(self, tool: MCPTool) -> PydanticTool:
        """Internal helper to wrap an MCP tool into a PydanticTool."""
        session = self.sessions.get(tool.name, None)
        if not session:
            raise RuntimeError(f"Session for tool {tool.name} not found")

        async def execute_tool(_ctx: RunContext, **kwargs: Any) -> Any:
            if not session:
                raise RuntimeError(f"Session for tool {tool.name} not found")
            result = await session.call_tool(
                tool.name,
                arguments=kwargs,
                progress_callback=print_progress_callback,
            )
            return result

        async def prepare_tool(
            _ctx: RunContext, tool_def: ToolDefinition
        ) -> ToolDefinition:
            # Inject the JSON schema from MCP directly into Pydantic AI
            tool_def.parameters_json_schema = tool.inputSchema
            return tool_def

        return PydanticTool(
            execute_tool,
            name=tool.name,
            description=tool.description or "",
            takes_ctx=True,  # Set to True to match the signature above
            prepare=prepare_tool,
        )

    async def cleanup(self):
        """Cleanly close all resources using AsyncExitStack."""
        await self.exit_stack.aclose()
