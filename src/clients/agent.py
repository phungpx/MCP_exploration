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

    try:
        while True:
            # Get user input
            user_input = input("\n[You] ")

            # Check if user wants to exit
            if user_input.lower() in ["exit", "quit", "bye", "goodbye"]:
                print("Goodbye!")
                break

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
