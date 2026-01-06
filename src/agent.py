import uuid
import asyncio
import argparse
from typing import Any

from rich.live import Live
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from langfuse import get_client
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings

from src.client import MCPClient
from src.settings import settings

langfuse = get_client()
if not langfuse.auth_check():
    print("Warning: Langfuse authentication failed.")

Agent.instrument_all()


class ChatSession:
    def __init__(self, user_id: str, session_id: str, client: MCPClient, agent: Agent):
        self.user_id = user_id
        self.session_id = session_id
        self.client = client
        self.agent = agent
        self.messages = []
        self.console = Console()

    async def handle_input(self, user_input: str) -> bool:
        """Processes user input. Returns False if the session should end."""
        user_input = user_input.strip()

        if user_input.lower() in ["exit", "quit"]:
            return False

        if user_input.startswith("/"):
            await self._handle_command(user_input)
        elif user_input.startswith("@"):
            await self._handle_resource(user_input)
        else:
            await self._chat_completion(user_input)

        return True

    async def _chat_completion(self, user_input: str):
        self.console.print("\n[bold blue]Assistant[/bold blue]")
        with Live("", console=self.console, vertical_overflow="visible") as live:
            async with self.agent.run_stream(
                user_input, message_history=self.messages
            ) as result:
                response_text = ""
                async for message in result.stream_text(delta=True):
                    response_text += message
                    live.update(Markdown(response_text))

                self.messages.extend(result.all_messages())

    async def _handle_command(self, user_input: str):
        parts = user_input.split()
        cmd = parts[0].lower()

        if cmd == "/prompts":
            await self._list_prompts()
        elif cmd == "/prompt":
            if len(parts) < 2:
                self.console.print("[yellow]Usage: /prompt <name> key=value[/yellow]")
                return

            prompt_name = parts[1]
            kwargs = dict(arg.split("=", 1) for arg in parts[2:] if "=" in arg)
            await self._execute_mcp_prompt(prompt_name, kwargs)
        else:
            self.console.print(f"[red]Unknown command: {cmd}[/red]")

    async def _handle_resource(self, user_input: str):
        topic = user_input[1:]
        # Mapping logic (simplified)
        resource_uri = "papers://folders" if topic == "folders" else f"papers://{topic}"

        # Strategy: Find session that supports this URI
        session = self.client.sessions.get(resource_uri)
        if not session and resource_uri.startswith("papers://"):
            session = next(
                (
                    _session
                    for _resource_uri, _session in self.client.sessions.items()
                    if _resource_uri.startswith("papers://")
                ),
                None,
            )

        if not session:
            self.console.print(f"[red]Resource '{resource_uri}' not found.[/red]")
            return

        try:
            result = await session.read_resource(uri=resource_uri)
            content = "\n".join([c.text for c in result.contents if hasattr(c, "text")])
            self.console.print(
                Panel(content, title=f"Resource: {resource_uri}", border_style="cyan")
            )
        except Exception as e:
            self.console.print(f"[red]Error reading resource: {e}[/red]")

    async def _list_prompts(self):
        if not self.client.list_prompts:
            self.console.print("[yellow]No prompts available.[/yellow]")
            return

        self.console.print("\n[bold]Available Prompts:[/bold]")
        for prompt in self.client.list_prompts:
            self.console.print(
                f"• [cyan]{prompt['name']}[/cyan] ({', '.join(prompt['arguments'].keys())}): {prompt.get('description', 'No description')}"
            )

    async def _execute_mcp_prompt(self, name: str, args: dict):
        session = self.client.sessions.get(name)
        if not session:
            self.console.print(f"[red]No session found for prompt: {name}[/red]")
            return

        result = await session.get_prompt(name, arguments=args)
        # Extract text using a more robust helper
        text = self._extract_text(result.messages[0].content)
        self.console.print(Panel(text, title=f"Prompt: {name}"))

    @staticmethod
    def _extract_text(content: Any) -> str:
        if isinstance(content, str):
            return content
        if hasattr(content, "text"):
            return content.text
        if isinstance(content, list):
            return " ".join(
                item.text if hasattr(item, "text") else str(item) for item in content
            )
        return str(content)


def get_model():
    return OpenAIChatModel(
        model_name=settings.llm.llm_model,
        provider=OpenAIProvider(
            base_url=settings.llm.llm_base_url,
            api_key=settings.llm.llm_api_key,
        ),
        settings=ModelSettings(
            temperature=settings.llm.llm_temperature,
            max_tokens=settings.llm.llm_max_tokens,
        ),
    )


async def init_system():
    client = MCPClient(config_path="server_config.json")
    await client.connect_to_servers()

    agent = Agent(
        model=get_model(),
        tools=client.list_tools,
        instrument=True,
    )
    return client, agent


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", default="default_user")
    parser.add_argument("--session-id", default=str(uuid.uuid4()))
    args = parser.parse_args()

    client, agent = await init_system()
    chat = ChatSession(args.user_id, args.session_id, client, agent)

    chat.console.print(
        Panel(
            f"User: {args.user_id}\nSession: {args.session_id}",
            title="MCP Agent Online",
            border_style="green",
        )
    )

    try:
        while True:
            user_input = chat.console.input("\n[bold green]You:[/bold green] ")
            should_continue = await chat.handle_input(user_input)
            if not should_continue:
                break
    except KeyboardInterrupt:
        chat.console.print("\n[yellow]Interrupted. Exiting...[/yellow]")
    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
