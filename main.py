import asyncio
from src.clients.agent import main as agent_main


def main():
    """Run the Research Agent client."""
    asyncio.run(agent_main())


if __name__ == "__main__":
    main()
