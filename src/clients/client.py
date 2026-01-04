import json
import shutil
import asyncio
import logging
from typing import Any, List
from pydantic_ai import RunContext, Tool as PydanticTool
from pydantic_ai.tools import ToolDefinition
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import Tool as MCPTool
from contextlib import AsyncExitStack


logging.basicConfig(
    level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s"
)


class MCPClient:
    def __init__(self) -> None:
        self.servers: List[MCPServer] = []
        self.config: dict[str, Any] = {}
        self.tools: List[Any] = []
        self.exit_stack = AsyncExitStack()

    def load_servers(self, config_path: str) -> None:
        """Load server configuration from a JSON file (typically mcp_config.json)
        and creates an instance of each server (no active connection until 'start' though).

        Args:
            config_path: Path to the JSON configuration file.
        """
        with open(config_path, mode="r", encoding="utf-8") as config_file:
            self.config = json.load(config_file)

        self.servers = [
            MCPServer(name, config)
            for name, config in self.config["mcpServers"].items()
        ]

    async def start(self) -> List[PydanticTool]:
        """Starts each MCP server and returns the tools for each server formatted for Pydantic AI."""
        self.tools = []
        for server in self.servers:
            try:
                await server.initialize()
                tools = await server.create_pydantic_ai_tools()
                self.tools += tools
            except Exception as e:
                logging.error(f"Failed to initialize server: {e}")
                await self.cleanup_servers()
                return []

        return self.tools

    async def cleanup_servers(self) -> None:
        """Clean up all servers properly."""
        for server in self.servers:
            try:
                await server.cleanup()
            except Exception as e:
                logging.warning(f"Warning during cleanup of server {server.name}: {e}")

    async def cleanup(self) -> None:
        """Clean up all resources including the exit stack."""
        try:
            # First clean up all servers
            await self.cleanup_servers()
            # Then close the exit stack
            await self.exit_stack.aclose()
        except Exception as e:
            logging.warning(f"Warning during final cleanup: {e}")


class MCPServer:
    def __init__(self, name: str, config: dict[str, Any]) -> None:
        self.name: str = name
        self.config: dict[str, Any] = config
        self.stdio_context: Any | None = None
        self.session: ClientSession | None = None
        self._cleanup_lock: asyncio.Lock = asyncio.Lock()
        self.exit_stack: AsyncExitStack = AsyncExitStack()

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
            env=self.config["env"] if self.config.get("env") else None,
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

    async def create_pydantic_ai_tools(self) -> list[PydanticTool]:
        """Convert MCP tools to pydantic_ai Tools."""
        tools = (await self.session.list_tools()).tools
        return [self.create_tool_instance(tool) for tool in tools]

    def create_tool_instance(self, tool: MCPTool) -> PydanticTool:
        """Initialize a Pydantic AI Tool from an MCP Tool."""

        async def execute_tool(**kwargs: Any) -> Any:
            return await self.session.call_tool(tool.name, arguments=kwargs)

        async def prepare_tool(
            ctx: RunContext, tool_def: ToolDefinition
        ) -> ToolDefinition | None:
            tool_def.parameters_json_schema = tool.inputSchema
            return tool_def

        return PydanticTool(
            execute_tool,
            name=tool.name,
            description=tool.description or "",
            takes_ctx=False,
            prepare=prepare_tool,
        )

    async def cleanup(self) -> None:
        """Clean up server resources."""
        async with self._cleanup_lock:
            try:
                await self.exit_stack.aclose()
                self.session = None
                self.stdio_context = None
            except Exception as e:
                logging.error(f"Error during cleanup of server {self.name}: {e}")
