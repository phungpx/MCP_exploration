import asyncio
import argparse
import uuid
from rich.live import Live
from rich.console import Console
from rich.markdown import Markdown

from langfuse import get_client

from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings
from pydantic_ai.tools import Tool as PydanticTool
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from src.client import MCPClient
from src.settings import settings

# Initialize Langfuse
langfuse = get_client()
if not langfuse.auth_check():
    print("Warning: Langfuse authentication failed.")

Agent.instrument_all()


def get_pydantic_llm_model():
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


async def init_agent():
    """Initialize Client and Agent."""
    client = MCPClient(config_path="server_config.json")
    await client.connect_to_servers()

    pydantic_model: OpenAIChatModel = get_pydantic_llm_model()
    # Note: Ensure client.list_tools is a list or property returning a list
    pydantic_tools: list[PydanticTool] = client.list_tools

    agent = Agent(
        model=pydantic_model,
        tools=pydantic_tools,
        instrument=True,  # langfuse observability
    )
    return client, agent


def parse_arguments():
    """Parse command line arguments for session and user configuration."""
    parser = argparse.ArgumentParser(description="MCP Agent CLI Chat")

    parser.add_argument(
        "--user-id",
        type=str,
        default="default_user",
        help="The ID of the user interacting with the agent.",
    )

    parser.add_argument(
        "--session-id",
        type=str,
        default=None,
        help="The Session ID for tracking. If not provided, a UUID will be generated.",
    )

    return parser.parse_args()


async def main():
    # 1. Configuration & Setup
    args = parse_arguments()
    user_id = args.user_id
    session_id = args.session_id or str(uuid.uuid4())

    console = Console()
    console.print(f"⏳ [bold]Initializing MCP Client and Agent...[/bold]")
    console.print(f"👤 [cyan]User ID:[/cyan] {user_id}")
    console.print(f"🆔 [cyan]Session ID:[/cyan] {session_id}")

    # 2. Initialize Agent
    mcp_client, mcp_agent = await init_agent()

    messages = []

    try:
        while True:
            try:
                user_input = console.input("\n[bold green]You:[/bold green] ")

                if user_input.lower() in ["exit", "quit"]:
                    console.print("[bold red]Goodbye![/bold red]")
                    break

                console.print("\n[bold blue][Assistant][/bold blue]")

                with Live(
                    "",
                    console=console,
                    vertical_overflow="visible",
                    refresh_per_second=15,
                ) as live:
                    # Run the agent stream
                    async with mcp_agent.run_stream(
                        user_input,
                        message_history=messages,
                        # If your pydantic-ai version supports run_context or similar metadata:
                        # run_context={"user_id": user_id, "session_id": session_id}
                    ) as result:
                        response_text = ""
                        async for message in result.stream_text(delta=True):
                            response_text += message
                            live.update(Markdown(response_text))

                        messages.extend(result.all_messages())

            except KeyboardInterrupt:
                console.print(
                    "\n[yellow]KeyboardInterrupt detected. Type 'exit' to quit.[/yellow]"
                )
                continue
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {e}")

    finally:
        await mcp_client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
