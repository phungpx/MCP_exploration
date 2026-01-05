import asyncio
from rich.live import Live
from rich.console import Console
from rich.markdown import Markdown

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings
from src.clients.client import MCPClient
from src.settings import settings


def get_model():
    llm_model = settings.llm.llm_model
    base_url = settings.llm.llm_base_url
    api_key = settings.llm.llm_api_key
    return OpenAIChatModel(
        model_name=llm_model,
        provider=OpenAIProvider(
            base_url=base_url,
            api_key=api_key,
        ),
        settings=ModelSettings(
            temperature=settings.llm.llm_temperature,
            max_tokens=settings.llm.llm_max_tokens,
        ),
    )


async def get_pydantic_ai_agent():
    client = MCPClient()
    client.load_servers("server_config.json")
    tools = await client.start()
    return client, Agent(model=get_model(), tools=tools)


async def main():
    mcp_client, mcp_agent = await get_pydantic_ai_agent()
    console = Console()
    messages = []

    # Display available prompts and resources at startup
    print("\n=== MCP Client Started ===")
    print(f"\n📝 Available Prompts: {len(mcp_client.list_available_prompts())}")
    for prompt_key in mcp_client.list_available_prompts():
        print(f"  - {prompt_key}")

    print(f"\n📚 Available Resources: {len(mcp_client.list_available_resources())}")
    for resource_key in mcp_client.list_available_resources():
        print(f"  - {resource_key}")

    print("\n💡 Commands:")
    print("  /prompts - List all available prompts")
    print("  /resources - List all available resources")
    print("  /use-prompt <key> - Use a specific prompt")
    print("  /read-resource <key> - Read a specific resource")
    print("  exit/quit - Exit the chat")
    print("=" * 50)

    try:
        while True:
            # Get user input
            user_input = input("\n[You] ")

            # Check if user wants to exit
            if user_input.lower() in ["exit", "quit", "bye", "goodbye"]:
                print("Goodbye!")
                break

            # Handle special commands
            if user_input.startswith("/prompts"):
                print("\n📝 Available Prompts:")
                for prompt_key in mcp_client.list_available_prompts():
                    prompt = mcp_client.prompts[prompt_key]
                    print(f"  - {prompt_key}")
                    if hasattr(prompt, "description") and prompt.description:
                        print(f"    Description: {prompt.description}")
                continue

            if user_input.startswith("/resources"):
                print("\n📚 Available Resources:")
                for resource_key in mcp_client.list_available_resources():
                    resource = mcp_client.resources[resource_key]
                    print(f"  - {resource_key}")
                    if hasattr(resource, "description") and resource.description:
                        print(f"    Description: {resource.description}")
                continue

            if user_input.startswith("/use-prompt "):
                prompt_key = user_input[12:].strip()
                try:
                    # Get the prompt (with no arguments for now)
                    prompt_text = await mcp_client.get_prompt(prompt_key)
                    print(f"\n📝 Prompt '{prompt_key}':\n")
                    print(prompt_text)
                    print(
                        "\n(You can copy this prompt and use it in your conversation)"
                    )
                except Exception as e:
                    print(f"\n[Error] {str(e)}")
                continue

            if user_input.startswith("/read-resource "):
                resource_key = user_input[15:].strip()
                try:
                    resource_content = await mcp_client.read_resource(resource_key)
                    print(f"\n📚 Resource '{resource_key}':\n")
                    console.print(Markdown(resource_content))
                except Exception as e:
                    print(f"\n[Error] {str(e)}")
                continue

            try:
                # Process the user input and output the response
                print("\n[Assistant]")
                with Live("", console=console, vertical_overflow="visible") as live:
                    async with mcp_agent.run_stream(
                        user_input, message_history=messages
                    ) as result:
                        curr_message = ""
                        async for message in result.stream_text(delta=True):
                            curr_message += message
                            live.update(Markdown(curr_message))

                    # Add the new messages to the chat history
                    messages.extend(result.all_messages())

            except Exception as e:
                print(f"\n[Error] An error occurred: {str(e)}")
    finally:
        # Ensure proper cleanup of MCP client resources when exiting
        await mcp_client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
