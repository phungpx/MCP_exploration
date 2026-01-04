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
                print(
                    f"\nConnected to {server_name} with tools:",
                    [t.name for t in tools_response.tools],
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
                print(f"Error {e}")
        except Exception as e:
            print(f"Failed to connect to {server_name}: {e}")

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
            print(f"Error loading server configuration: {e}")
            raise

    async def process_query(self, query):
        messages = [{"role": "user", "content": query}]
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
                print(assistant_message.content)

            messages.append(assistant_message)

            # Check if there are tool calls
            if assistant_message.tool_calls:
                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)

                    print(f"Calling tool `{tool_name}` with arguments`{tool_args}`")

                    # Call a tool through the client session
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

    async def list_prompts(self):
        """List all available prompts."""
        if not self.available_prompts:
            print("No prompts available.")
            return

        print("\nAvailable prompts:")
        for prompt in self.available_prompts:
            print(f"- {prompt['name']}: {prompt['description']}")
            if prompt["arguments"]:
                print(f"  Arguments:")
                for arg in prompt["arguments"]:
                    arg_name = arg.name if hasattr(arg, "name") else arg.get("name", "")
                    print(f"    - {arg_name}")

    async def execute_prompt(self, prompt_name, args):
        """Execute a prompt with the given arguments."""
        session = self.sessions.get(prompt_name)
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
                await self.process_query(text)
        except Exception as e:
            print(f"Error: {e}")

    async def chat_loop(self):
        print("\nMCP Chatbot Started!")
        print("Type your queries or 'quit' to exit.")
        print("Use @folders to see available topics")
        print("Use @<topic> to search papers in that topic")
        print("Use /prompts to list available prompts")
        print("Use /prompt <name> <arg1=value1> to execute a prompt")

        while True:
            try:
                query = input("\nQuery: ").strip()
                if not query:
                    continue

                if query.lower() == "quit":
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
                            print("Usage: /prompt <name> <arg1=value1> <arg2=value2>")
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
                        print(f"Unknown command: {command}")
                    continue

                await self.process_query(query)

            except Exception as e:
                print(f"\nError: {str(e)}")

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
