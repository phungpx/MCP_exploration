import uuid
import asyncio
import argparse
from rich.live import Live
from rich.console import Console
from rich.markdown import Markdown

from mcp import ClientSession
from langfuse import get_client
from typing import Optional

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


async def get_prompts(available_prompts: Optional[list[dict]] = None):
    if not available_prompts:
        print("No prompts available.")
        return

    print("\nAvailable prompts:")
    for prompt in available_prompts:
        print(f"- {prompt['name']}: {prompt['description']}")
        if prompt["arguments"]:
            print("\tArguments:")
            for arg in prompt["arguments"]:
                arg_name = arg.name if hasattr(arg, "name") else arg.get("name", "")
                print(f"\t\t-{arg_name}")


async def execute_prompt(
    sessions: dict[str, ClientSession],
    prompt_name: str,
    args: dict,
):
    session = sessions.get(prompt_name)
    if not session:
        print(f"Prompt '{prompt_name}' not found.")
        return

    try:
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
            print(f"\nExecuting prompt '{prompt_name}'...")
            # await execute_query(console, orchestrator, text, messages)
            print(text)
    except Exception as e:
        print(f"Error: {e}")


async def get_resource(sessions: dict[str, ClientSession], resource_uri: str):
    session = sessions.get(resource_uri)

    # Fallback for papers URIs - try any papers resource session
    if not session and resource_uri.startswith("papers://"):
        for resounce_uri, _session in sessions.items():
            if resounce_uri.startswith("papers://"):
                session = _session
                break

    if not session:
        print(f"Resource '{resource_uri}' not found.")
        return

    try:
        result = await session.read_resource(uri=resource_uri)
        if result and result.contents:
            print(f"\nResource: {resource_uri}")
            print("Content:")
            print(result.contents[0].text)
        else:
            print("No content available.")
    except Exception as e:
        print(f"Error: {e}")


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

                # Check for @resource syntax first
                if user_input.startswith("@"):
                    topic = user_input[1:]  # Remove @ sign
                    if topic == "folders":
                        resource_uri = "papers://folders"
                    else:
                        resource_uri = f"papers://{topic}"
                    await get_resource(mcp_client.sessions, resource_uri)
                    continue

                # Check for /command syntax
                if user_input.startswith("/"):
                    parts = user_input.split()
                    command = parts[0].lower()
                    if command == "/prompts":
                        await get_prompts(mcp_client.list_prompts)
                    elif command == "/prompt":
                        if len(parts) < 2:
                            print("Usage: /prompt <name> <arg1=value1> <arg2=value2>")
                            continue

                        prompt_name = parts[1]
                        args = {}

                        # Parse arguments
                        for arg in parts[2:]:
                            if "=" in arg:
                                key, value = arg.split("=", 1)
                                args[key] = value

                        await execute_prompt(mcp_client.sessions, prompt_name, args)
                    else:
                        print(f"Unknown command: {command}")
                    continue

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
