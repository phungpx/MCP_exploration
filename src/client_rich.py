import os
import json
import asyncio
import nest_asyncio
from dotenv import load_dotenv
from openai import AsyncOpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack
from openai.types.chat.chat_completion_function_tool_param import (
    ChatCompletionFunctionToolParam,
)
from openai.types.chat.chat_completion_tool_message_param import (
    ChatCompletionToolMessageParam,
)
from rich import box
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.console import Console
from rich.markdown import Markdown

nest_asyncio.apply()

load_dotenv("/Users/phung.pham/Documents/PHUNGPX/LVLM-tutorials/mcp_anthropic/.env")


class MCPCompatibleChatbot:
    def __init__(self, model_name: str, api_key: str, base_url: str):
        self.model_name = model_name
        self.llm_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.exit_stack = AsyncExitStack()
        self.available_tools: list[ChatCompletionFunctionToolParam] = []
        self.available_prompts = []
        self.sessions: dict[str, ClientSession] = {}
        self.console = Console()

    async def connect_to_server(self, server_name: str, server_config: dict) -> None:
        """Connect to a single MCP server."""
        try:
            server_params = StdioServerParameters(**server_config)
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            read, write = stdio_transport
            session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )
            await session.initialize()
            # self.sessions.append(session)

            try:
                # List available tools for this session
                tools_response = await session.list_tools()
                tool_names = [t.name for t in tools_response.tools]
                self.console.print(
                    Panel(
                        f"[bold green]Connected to {server_name}[/bold green]\n"
                        f"Available tools: [cyan]{', '.join(tool_names)}[/cyan]",
                        title="✓ Server Connected",
                        border_style="green",
                        box=box.ROUNDED,
                    )
                )

                for tool in tools_response.tools:
                    self.sessions[tool.name] = session
                    self.available_tools.append(
                        {
                            "type": "function",
                            "function": {
                                "name": tool.name,
                                "description": tool.description,
                                "parameters": tool.inputSchema,
                            },
                        }
                    )
                # List available prompts
                prompts_response = await session.list_prompts()
                if prompts_response and prompts_response.prompts:
                    for prompt in prompts_response.prompts:
                        self.sessions[prompt.name] = session
                        self.available_prompts.append(
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
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")

        except Exception as e:
            self.console.print(
                Panel(
                    f"[bold red]Failed to connect to {server_name}[/bold red]\n{e}",
                    title="✗ Connection Error",
                    border_style="red",
                    box=box.ROUNDED,
                )
            )

    async def connect_to_servers(self):
        """Connect to all configured MCP servers."""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            with open(
                os.path.join(current_dir, "server_config.json"), mode="r"
            ) as file:
                data = json.load(file)
            servers = data.get("mcpServers", {})
            for server_name, server_config in servers.items():
                await self.connect_to_server(server_name, server_config)
        except Exception as e:
            self.console.print(
                f"[bold red]Error loading server configuration: {e}[/bold red]"
            )
            raise

    async def process_query(self, query):
        messages = [{"role": "user", "content": query}]

        # Show thinking indicator
        with self.console.status("[bold cyan]Thinking...", spinner="dots"):
            response = await self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=self.available_tools if self.available_tools else None,
                tool_choice="auto",
            )

        process_query = True
        while process_query:
            assistant_message = response.choices[0].message
            # Check if there's text content
            if assistant_message.content:
                self.console.print(
                    Panel(
                        Markdown(assistant_message.content),
                        title="🤖 Assistant",
                        border_style="blue",
                        box=box.ROUNDED,
                    )
                )

            messages.append(assistant_message)

            # Check if there are tool calls
            if assistant_message.tool_calls:
                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)

                    # Display tool call with syntax highlighting
                    tool_info = f"Tool: {tool_name}\nArguments:\n{json.dumps(tool_args, indent=2)}"
                    self.console.print(
                        Panel(
                            Syntax(
                                tool_info, "json", theme="monokai", line_numbers=False
                            ),
                            title="🔧 Tool Call",
                            border_style="yellow",
                            box=box.ROUNDED,
                        )
                    )

                    # Call a tool through the client session
                    with self.console.status(
                        f"[bold yellow]Executing {tool_name}...", spinner="dots"
                    ):
                        session = self.sessions[tool_name]
                        tool_result = await session.call_tool(
                            name=tool_name,
                            arguments=tool_args,
                        )

                    # Handle result content - MCP returns a list of content items (e.g., TextContent objects)
                    # Each content item has a .text attribute
                    if (
                        isinstance(tool_result.content, list)
                        and len(tool_result.content) > 0
                    ):
                        # Extract text from each content item and join them
                        content_parts = []
                        for item in tool_result.content:
                            if hasattr(item, "text"):
                                content_parts.append(item.text)
                            elif isinstance(item, str):
                                content_parts.append(item)
                            else:
                                content_parts.append(str(item))
                        tool_content = "\n".join(content_parts)
                    elif isinstance(tool_result.content, str):
                        tool_content = tool_result.content
                    else:
                        tool_content = str(tool_result.content)

                    # Add tool result to messages (OpenAI format uses role "tool")
                    messages.append(
                        ChatCompletionToolMessageParam(
                            role="tool",
                            tool_call_id=tool_call.id,
                            content=tool_content,
                        ),
                    )

                # Get next response from OpenAI
                with self.console.status(
                    "[bold cyan]Processing results...", spinner="dots"
                ):
                    response = await self.llm_client.chat.completions.create(
                        model=self.model_name,
                        messages=messages,
                        tools=self.available_tools if self.available_tools else None,
                        tool_choice="auto",
                    )
            else:
                # No tool calls, conversation complete
                process_query = False

    async def get_resource(self, resource_uri):
        session = self.sessions.get(resource_uri)
        # Fallback for papers URIs - try any papers resource session
        if not session and resource_uri.startswith("papers://"):
            for uri, sess in self.sessions.items():
                if uri.startswith("papers://"):
                    session = sess
                    break

        if not session:
            self.console.print(f"[red]Resource '{resource_uri}' not found.[/red]")
            return

        try:
            with self.console.status(f"[bold cyan]Loading resource...", spinner="dots"):
                result = await session.read_resource(uri=resource_uri)

            if result and result.contents:
                content = result.contents[0].text
                # Try to parse as JSON for better display
                try:
                    json_content = json.loads(content)
                    formatted_content = json.dumps(json_content, indent=2)
                    self.console.print(
                        Panel(
                            Syntax(
                                formatted_content,
                                "json",
                                theme="monokai",
                                line_numbers=False,
                            ),
                            title=f"📄 Resource: {resource_uri}",
                            border_style="cyan",
                            box=box.ROUNDED,
                        )
                    )
                except json.JSONDecodeError:
                    # Not JSON, display as markdown
                    self.console.print(
                        Panel(
                            Markdown(content),
                            title=f"📄 Resource: {resource_uri}",
                            border_style="cyan",
                            box=box.ROUNDED,
                        )
                    )
            else:
                self.console.print("[yellow]No content available.[/yellow]")
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")

    async def list_prompts(self):
        """List all available prompts."""
        if not self.available_prompts:
            self.console.print("[yellow]No prompts available.[/yellow]")
            return

        table = Table(
            title="📝 Available Prompts",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")
        table.add_column("Arguments", style="yellow")

        for prompt in self.available_prompts:
            args_list = []
            if prompt["arguments"]:
                for arg in prompt["arguments"]:
                    arg_name = arg.name if hasattr(arg, "name") else arg.get("name", "")
                    args_list.append(arg_name)

            args_str = ", ".join(args_list) if args_list else "None"
            table.add_row(prompt["name"], prompt["description"], args_str)

        self.console.print(table)

    async def execute_prompt(self, prompt_name, args):
        """Execute a prompt with the given arguments."""
        session = self.sessions.get(prompt_name)
        if not session:
            self.console.print(f"[red]Prompt '{prompt_name}' not found.[/red]")
            return

        try:
            with self.console.status(
                f"[bold cyan]Executing prompt '{prompt_name}'...", spinner="dots"
            ):
                result = await session.get_prompt(prompt_name, arguments=args)

            if result and result.messages:
                prompt_content = result.messages[0].content

                # Extract text from content (handles different formats)
                if isinstance(prompt_content, str):
                    text = prompt_content
                elif hasattr(prompt_content, "text"):
                    text = prompt_content.text
                else:
                    # Handle list of content items
                    text = " ".join(
                        item.text if hasattr(item, "text") else str(item)
                        for item in prompt_content
                    )

                self.console.print(
                    Panel(
                        f"[green]Prompt: {prompt_name}[/green]\n"
                        f"[dim]Arguments: {args if args else 'None'}[/dim]",
                        title="▶ Executing Prompt",
                        border_style="green",
                        box=box.ROUNDED,
                    )
                )
                await self.process_query(text)
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")

    async def chat_loop(self):
        # Display welcome message
        welcome_text = """
[bold cyan]Welcome to MCP Chatbot![/bold cyan]

[bold]Commands:[/bold]
  • Type your queries naturally
  • [yellow]@folders[/yellow] - See available topics
  • [yellow]@<topic>[/yellow] - Search papers in that topic
  • [yellow]/prompts[/yellow] - List available prompts
  • [yellow]/prompt <name> <arg1=value1>[/yellow] - Execute a prompt
  • [red]quit[/red] - Exit the chatbot
        """
        self.console.print(
            Panel(
                welcome_text,
                title="🤖 MCP Chatbot",
                border_style="bright_blue",
                box=box.DOUBLE,
                padding=(1, 2),
            )
        )

        while True:
            try:
                # Use rich text for prompt
                self.console.print()
                query = self.console.input("[bold green]❯[/bold green] ").strip()
                if not query:
                    continue

                if query.lower() == "quit":
                    self.console.print(
                        Panel(
                            "[bold cyan]Thank you for using MCP Chatbot! Goodbye! 👋[/bold cyan]",
                            border_style="bright_blue",
                            box=box.ROUNDED,
                        )
                    )
                    break

                # Check for @resource syntax first
                if query.startswith("@"):
                    # Remove @ sign
                    topic = query[1:]
                    if topic == "folders":
                        resource_uri = "papers://folders"
                    else:
                        resource_uri = f"papers://{topic}"
                    await self.get_resource(resource_uri)
                    continue

                # Check for /command syntax
                if query.startswith("/"):
                    parts = query.split()
                    command = parts[0].lower()
                    if command == "/prompts":
                        await self.list_prompts()
                    elif command == "/prompt":
                        if len(parts) < 2:
                            self.console.print(
                                "[yellow]Usage: /prompt <name> <arg1=value1> <arg2=value2>[/yellow]"
                            )
                            continue

                        prompt_name = parts[1]
                        args = {}

                        # Parse arguments
                        for arg in parts[2:]:
                            if "=" in arg:
                                key, value = arg.split("=", 1)
                                args[key] = value

                        await self.execute_prompt(prompt_name, args)
                    else:
                        self.console.print(f"[red]Unknown command: {command}[/red]")
                    continue

                await self.process_query(query)

            except KeyboardInterrupt:
                self.console.print("\n[yellow]Interrupted by user[/yellow]")
                continue
            except Exception as e:
                self.console.print(
                    Panel(
                        f"[bold red]Error:[/bold red] {str(e)}",
                        title="⚠ Error",
                        border_style="red",
                        box=box.ROUNDED,
                    )
                )

    async def cleanup(self):
        """Cleanly close all resources using AsyncExitStack."""
        await self.exit_stack.aclose()


async def main():
    chatbot_client = MCPCompatibleChatbot(
        model_name=os.getenv("LLM_MODEL"),
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL"),
    )
    try:
        # the mcp clients and sessions are not initialized using "with"
        # like in the previous lesson
        # so the cleanup should be manually handled
        await chatbot_client.connect_to_servers()
        await chatbot_client.chat_loop()
    finally:
        await chatbot_client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
