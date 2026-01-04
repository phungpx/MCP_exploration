"""Main entry point for the Calendar Reminder Agent."""

import asyncio
from src.client import main as client_main


def main():
    """Run the Calendar Reminder Agent client."""
    asyncio.run(client_main())


if __name__ == "__main__":
    main()
