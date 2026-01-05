import os
import asyncio
import sys
from openai import AsyncOpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import CreateMessageResult, TextContent
from dotenv import load_dotenv

load_dotenv("/Users/phung.pham/Documents/PHUNGPX/MCP_exploration/.env")

# 1. Setup OpenAI Client
llm_client = AsyncOpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
)


async def run_client():
    # 2. Server connection parameters
    server_params = StdioServerParameters(
        command=sys.executable,  # Use the same Python interpreter as the client
        args=["server.py"],  # Name of your server file
        cwd="/Users/phung.pham/Documents/PHUNGPX/MCP_exploration/scripts/sampling",
    )

    # 3. Define the OpenAI Sampling Handler
    async def handle_sampling_request(context, params):
        print(
            f"\n[Client] Server requested sampling for: {params.messages[0].content.text}"
        )

        # Convert MCP SamplingMessages to OpenAI Chat format
        openai_messages = []
        for msg in params.messages:
            openai_messages.append({"role": msg.role, "content": msg.content.text})

        # Call OpenAI API
        response = await llm_client.chat.completions.create(
            model="gemini-2.0-flash-exp",
            messages=openai_messages,
            max_tokens=params.maxTokens or 150,
        )

        # Send the result back to the MCP Server
        return CreateMessageResult(
            role="assistant",
            content=TextContent(type="text", text=response.choices[0].message.content),
            model=os.getenv("LLM_MODEL"),
        )

    async with stdio_client(server_params) as (read, write):
        # Pass sampling_callback to ClientSession constructor
        async with ClientSession(
            read, write, sampling_callback=handle_sampling_request
        ) as session:
            await session.initialize()

            # 4. Trigger the tool
            print("--- Calling generate_poem via MCP Server ---")
            result = await session.call_tool(
                "generate_poem", arguments={"topic": "artificial intelligence"}
            )

            print("\n--- Resulting Poem ---")
            print(result.content[0].text)


if __name__ == "__main__":
    asyncio.run(run_client())
