import os
import json
import asyncio
import sys
from openai import AsyncOpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import CreateMessageResult, TextContent
from contextlib import AsyncExitStack
from dotenv import load_dotenv

load_dotenv(".env")


class MCPClient:
    def __init__(self):
        self.exit_stack = AsyncExitStack()
        self.session: ClientSession = None
        self.tools: list[dict] = []
        self.llm_client = AsyncOpenAI(
            api_key=os.getenv("LLM_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL"),
        )

    async def connect_to_server(self):
        server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "scripts.sampling.server"],
            # cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        read, write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(
                read_stream=read,
                write_stream=write,
                sampling_callback=self.handle_sampling_request,  # Sampling callback for the server
            )
        )
        await self.session.initialize()

        try:
            # List available tools for this session
            tools_response = await self.session.list_tools()
            print(
                f"\nConnected to sampling server with tools:",
                [t.name for t in tools_response.tools],
            )

            for tool in tools_response.tools:
                self.tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.inputSchema,
                        },
                    }
                )
        except Exception as e:
            print(f"Error connecting to MCP server: {e}")

    # Define the Sampling Callback Handler
    # This is used to handle the sampling request from the MCP Server
    async def handle_sampling_request(self, context, params):
        print(
            f"\n[Client] Server requested sampling for: {params.messages[0].content.text}"
        )

        # Convert MCP SamplingMessages to OpenAI Chat format
        openai_messages = []
        for msg in params.messages:
            openai_messages.append(
                {"role": msg.role, "content": msg.content.text},
            )

        # Call OpenAI API
        response = await self.llm_client.chat.completions.create(
            model="gemini-2.0-flash",
            messages=openai_messages,
            max_tokens=params.maxTokens or 150,
        )

        # Send the result back to the MCP Server
        return CreateMessageResult(
            role="assistant",
            content=TextContent(
                type="text",
                text=response.choices[0].message.content,
            ),
            model=os.getenv("LLM_MODEL"),
        )

    async def run(self):
        # 4. Trigger the tool
        print("--- Calling generate_poem via MCP Server ---")
        result = await self.session.call_tool(
            "generate_poem", arguments={"topic": "artificial intelligence"}
        )

        print("\n--- Resulting Poem ---")
        print(result.content[0].text)

    async def close(self):
        await self.exit_stack.aclose()

    async def simple_react(self, message: str):
        messages = [{"role": "user", "content": message}]
        response = await self.llm_client.chat.completions.create(
            model=os.getenv("LLM_MODEL"),
            messages=messages,
            tools=self.tools,
            tool_choice="auto",
        )

        while True:
            assistant_msg = response.choices[0].message
            if assistant_msg.content:
                print(assistant_msg.content)

            messages.append(assistant_msg)

            if assistant_msg.tool_calls:
                for tool_call in assistant_msg.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    print(f"Calling tool `{tool_name}` with arguments`{tool_args}`")
                    tool_result = await self.session.call_tool(tool_name, tool_args)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": tool_result.content,
                        }
                    )
                response = await self.llm_client.chat.completions.create(
                    model=os.getenv("LLM_MODEL"),
                    messages=messages,
                    tools=self.tools if self.tools else None,
                    tool_choice="auto",
                )
            else:
                break

    async def chat(self):
        while True:
            try:
                query = input("\nQuery: ").strip()
                if not query:
                    continue

                if query.lower() == "quit":
                    break
                await self.simple_react(query)
            except Exception as e:
                print(f"Error: {e}")


async def main():
    try:
        client = MCPClient()
        await client.connect_to_server()
        await client.chat()
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
