import sys
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import LoggingMessageNotificationParams


async def logging_callback(params: LoggingMessageNotificationParams):
    print(params.data)


async def print_progress_callback(
    progress: float, total: float | None, message: str | None
):
    if total is not None:
        percentage = (progress / total) * 100
        print(f"Progress: {progress}/{total} ({percentage:.1f}%)")
    else:
        print(f"Progress: {progress}")


async def run_client():
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "scripts.notification.server"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(
            read,
            write,
            logging_callback=logging_callback,
        ) as session:
            await session.initialize()

            result = await session.call_tool(
                "process_data",
                arguments={"data": "Hello World"},
                progress_callback=print_progress_callback,
            )
            print(f"Result: {result.content[0].text}")


if __name__ == "__main__":
    asyncio.run(run_client())
