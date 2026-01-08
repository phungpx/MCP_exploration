"""Client for interacting with the elicitation server.

This client demonstrates how to handle both form and URL mode elicitation:
- Form mode: Collects structured data through a schema
- URL mode: Directs users to external URLs for sensitive operations
"""

import asyncio
from typing import Any, Dict

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def handle_form_elicitation(elicit_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle form mode elicitation by collecting user input."""
    print("\n" + "=" * 60)
    print("FORM ELICITATION REQUIRED")
    print("=" * 60)
    print(f"Message: {elicit_data.get('message', 'Input required')}")
    print("\nSchema:", elicit_data.get("schema", {}))

    # In a real application, you would collect user input based on the schema
    # For this demo, we'll simulate user responses

    # Get the schema properties
    schema = elicit_data.get("schema", {})
    properties = schema.get("properties", {})

    print("\n--- User Response (simulated) ---")

    # Simulate user choosing to check alternative date
    response_data = {}
    for prop_name, prop_details in properties.items():
        print(f"\n{prop_details.get('description', prop_name)}")

        if prop_name == "checkAlternative":
            # Simulate user accepting alternative
            user_input = "yes"
            print(f"  → {user_input}")
            response_data[prop_name] = True
        elif prop_name == "alternativeDate":
            # Use default or simulate user input
            default_val = prop_details.get("default", "2024-12-26")
            print(f"  → {default_val}")
            response_data[prop_name] = default_val

    return {"action": "accept", "data": response_data}  # or "decline"/"cancel"


async def handle_url_elicitation(elicit_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle URL mode elicitation by prompting user to visit URL."""
    print("\n" + "=" * 60)
    print("URL ELICITATION REQUIRED")
    print("=" * 60)
    print(f"Message: {elicit_data.get('message', 'External action required')}")
    print(f"URL: {elicit_data.get('url', 'N/A')}")
    print(f"Elicitation ID: {elicit_data.get('elicitationId', 'N/A')}")
    print("\nPlease complete the action in your browser.")
    print("=" * 60)

    # Simulate user accepting the URL elicitation
    # In a real app, the user would visit the URL and confirm
    user_choice = (
        input("\nDid you complete the action? (accept/decline/cancel): ")
        .strip()
        .lower()
    )

    if user_choice not in ["accept", "decline", "cancel"]:
        user_choice = "accept"  # Default for demo

    return {"action": user_choice}


async def handle_elicitation_request(context, params) -> Dict[str, Any]:
    """Handle elicitation request by collecting user input."""
    print("\n" + "=" * 60)
    print("ELICITATION REQUEST REQUIRED")
    print("=" * 60)
    print(f"Message: {params.get('message', 'Input required')}")
    print("\nSchema:", params.get("schema", {}))
    return {"action": "accept", "data": params.get("data", {})}


async def call_tool_with_elicitation(
    session: ClientSession, tool_name: str, arguments: Dict[str, Any]
) -> None:
    """Call a tool and handle any elicitation requests."""
    print(f"\n{'=' * 60}")
    print(f"Calling tool: {tool_name}")
    print(f"Arguments: {arguments}")
    print("=" * 60)

    try:
        # Make the initial tool call
        result = await session.call_tool(tool_name, arguments=arguments)

        # Check if elicitation is required
        if hasattr(result, "elicit") and result.elicit:
            print("\n⚠️  Elicitation required!")

            for elicit_req in result.elicit:
                mode = elicit_req.get("mode", "unknown")

                if mode == "form":
                    # Handle form mode elicitation
                    elicit_response = await handle_form_elicitation(elicit_req)

                    # Submit the elicitation response
                    elicitation_id = elicit_req.get("elicitationId")
                    final_result = await session.submit_elicitation(
                        elicitation_id=elicitation_id, response=elicit_response
                    )

                    print("\n✅ Final Result:", final_result)

                elif mode == "url":
                    # Handle URL mode elicitation
                    elicit_response = await handle_url_elicitation(elicit_req)

                    # Submit the elicitation response
                    elicitation_id = elicit_req.get("elicitationId")
                    final_result = await session.submit_elicitation(
                        elicitation_id=elicitation_id, response=elicit_response
                    )

                    print("\n✅ Final Result:", final_result)
                else:
                    print(f"Unknown elicitation mode: {mode}")
        else:
            # No elicitation needed, just print the result
            print("\n✅ Result:", result)

    except Exception as e:
        # Check if this is a UrlElicitationRequiredError (error code -32042)
        if hasattr(e, "code") and e.code == -32042:
            print("\n⚠️  URL Elicitation Required (via error)")

            # The error data contains elicitation parameters
            if hasattr(e, "data") and e.data:
                for elicit_req in e.data:
                    elicit_response = await handle_url_elicitation(elicit_req)

                    # Submit the elicitation response and retry
                    elicitation_id = elicit_req.get("elicitationId")
                    final_result = await session.submit_elicitation(
                        elicitation_id=elicitation_id, response=elicit_response
                    )

                    print("\n✅ Final Result:", final_result)
        else:
            print(f"\n❌ Error: {e}")


async def main():
    """Main function to run the elicitation client examples."""
    # Set up the server parameters
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "scripts.elicitation.server"],
    )

    print("🚀 Starting Elicitation Client Demo")
    print("=" * 60)

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(
            read,
            write,
            elicitation_callback=handle_form_elicitation,
        ) as session:
            # Initialize the session
            await session.initialize()

            print("\n📋 Available tools:")
            tools_result = await session.list_tools()
            for tool in tools_result.tools:
                print(f"  - {tool.name}: {tool.description}")

            # Example 1: Book a table for an available date (no elicitation)
            print("\n\n" + "=" * 60)
            print("EXAMPLE 1: Booking available date (no elicitation)")
            print("=" * 60)
            await call_tool_with_elicitation(
                session,
                "book_table",
                {"date": "2024-12-20", "time": "19:00", "party_size": 4},
            )

            # Example 2: Book a table for unavailable date (form elicitation)
            print("\n\n" + "=" * 60)
            print("EXAMPLE 2: Booking unavailable date (form elicitation)")
            print("=" * 60)
            await call_tool_with_elicitation(
                session,
                "book_table",
                {"date": "2024-12-25", "time": "19:00", "party_size": 4},
            )

            # Example 3: Secure payment (URL elicitation via ctx.elicit_url)
            print("\n\n" + "=" * 60)
            print("EXAMPLE 3: Secure payment (URL elicitation)")
            print("=" * 60)
            await call_tool_with_elicitation(
                session, "secure_payment", {"amount": 150.00}
            )

            # Example 4: Connect service (URL elicitation via error)
            print("\n\n" + "=" * 60)
            print("EXAMPLE 4: Connect service (URL elicitation via error)")
            print("=" * 60)
            await call_tool_with_elicitation(
                session, "connect_service", {"service_name": "github"}
            )

            print("\n\n✅ All examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
