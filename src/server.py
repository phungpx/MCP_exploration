import json
import os
from datetime import datetime, timedelta
from typing import List, Optional
from mcp.server.fastmcp import FastMCP

from src.models import Reminder, EventDetails, NotificationSettings, ReminderStatus
from src.calendar_integration import GoogleCalendarIntegration
from src.settings import settings

REMINDER_DIR = settings.save_dir

# Initialize FastMCP server
mcp = FastMCP("reminder_agent")

# Initialize Google Calendar integration
calendar_integration = GoogleCalendarIntegration()


def _get_reminders_file() -> str:
    """Get path to reminders JSON file."""
    os.makedirs(REMINDER_DIR, exist_ok=True)
    return os.path.join(REMINDER_DIR, "reminders.json")


def _load_reminders() -> dict[str, Reminder]:
    """Load all reminders from storage."""
    file_path = _get_reminders_file()
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
            return {id: Reminder.from_dict(r) for id, r in data.items()}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_reminders(reminders: dict[str, Reminder]) -> None:
    """Save all reminders to storage."""
    file_path = _get_reminders_file()
    data = {id: r.to_dict() for id, r in reminders.items()}
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)


@mcp.tool()
def create_reminder(
    title: str,
    datetime_str: str,
    attendees: Optional[List[str]] = None,
    location: Optional[str] = None,
    description: Optional[str] = None,
    notification_minutes: Optional[List[int]] = None,
) -> str:
    """
    Create a new calendar reminder.

    Args:
        title: Event title
        datetime_str: Event date and time in ISO format (e.g., "2024-12-25T14:30:00")
        attendees: List of attendee email addresses (optional)
        location: Event location (optional)
        description: Event description (optional)
        notification_minutes: Minutes before event to send notifications (optional, defaults to [60, 1440])

    Returns:
        JSON string with created reminder information
    """
    try:
        # Parse datetime
        event_datetime = datetime.fromisoformat(datetime_str)

        # Create event details
        event = EventDetails(
            title=title,
            datetime=event_datetime,
            attendees=attendees or [],
            location=location,
            description=description,
        )

        # Create notification settings
        notification_settings = NotificationSettings(
            minutes_before=notification_minutes or [60, 1440]
        )

        # Create reminder
        reminder = Reminder(
            event=event,
            notification_settings=notification_settings,
        )

        # Load existing reminders and add new one
        reminders = _load_reminders()
        reminders[reminder.id] = reminder
        _save_reminders(reminders)

        result = {
            "success": True,
            "reminder_id": reminder.id,
            "message": f"Reminder created successfully for '{title}' on {event_datetime.strftime('%Y-%m-%d at %H:%M')}",
            "details": reminder.to_dict(),
        }

        return json.dumps(result, indent=2)

    except ValueError as e:
        return json.dumps(
            {
                "success": False,
                "error": f"Invalid datetime format: {str(e)}. Use ISO format like '2024-12-25T14:30:00'",
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def get_reminder(reminder_id: str) -> str:
    """
    Get details of a specific reminder.

    Args:
        reminder_id: The ID of the reminder to retrieve

    Returns:
        JSON string with reminder information
    """
    reminders = _load_reminders()

    if reminder_id not in reminders:
        return json.dumps(
            {"success": False, "error": f"Reminder with ID '{reminder_id}' not found"},
            indent=2,
        )

    reminder = reminders[reminder_id]
    return json.dumps({"success": True, "reminder": reminder.to_dict()}, indent=2)


@mcp.tool()
def list_reminders(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[str] = None,
) -> str:
    """
    List reminders with optional filtering.

    Args:
        start_date: Filter by start date (ISO format, optional)
        end_date: Filter by end date (ISO format, optional)
        status: Filter by status: pending, notified, completed, cancelled (optional)

    Returns:
        JSON string with list of reminders
    """
    try:
        reminders = _load_reminders()

        # Apply filters
        filtered = []
        for reminder in reminders.values():
            # Status filter
            if status and reminder.status.value != status.lower():
                continue

            # Date range filter
            if start_date:
                start = datetime.fromisoformat(start_date)
                if reminder.event.datetime < start:
                    continue

            if end_date:
                end = datetime.fromisoformat(end_date)
                if reminder.event.datetime > end:
                    continue

            filtered.append(reminder.to_dict())

        # Sort by datetime
        filtered.sort(key=lambda r: r["event"]["datetime"])

        return json.dumps(
            {"success": True, "count": len(filtered), "reminders": filtered}, indent=2
        )

    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def update_reminder(
    reminder_id: str,
    title: Optional[str] = None,
    datetime_str: Optional[str] = None,
    attendees: Optional[List[str]] = None,
    location: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
) -> str:
    """
    Update an existing reminder.

    Args:
        reminder_id: The ID of the reminder to update
        title: New event title (optional)
        datetime_str: New event datetime in ISO format (optional)
        attendees: New list of attendee email addresses (optional)
        location: New event location (optional)
        description: New event description (optional)
        status: New status: pending, notified, completed, cancelled (optional)

    Returns:
        JSON string with update result
    """
    try:
        reminders = _load_reminders()

        if reminder_id not in reminders:
            return json.dumps(
                {
                    "success": False,
                    "error": f"Reminder with ID '{reminder_id}' not found",
                },
                indent=2,
            )

        reminder = reminders[reminder_id]

        # Update fields
        if title:
            reminder.event.title = title
        if datetime_str:
            reminder.event.datetime = datetime.fromisoformat(datetime_str)
        if attendees is not None:
            reminder.event.attendees = attendees
        if location is not None:
            reminder.event.location = location
        if description is not None:
            reminder.event.description = description
        if status:
            reminder.status = ReminderStatus(status.lower())

        reminder.update_timestamp()

        # Save changes
        reminders[reminder_id] = reminder
        _save_reminders(reminders)

        # Update in Google Calendar if synced
        if reminder.calendar_synced:
            success, error = calendar_integration.update_event(reminder)
            if not success:
                return json.dumps(
                    {
                        "success": True,
                        "reminder": reminder.to_dict(),
                        "warning": f"Reminder updated locally but failed to sync to Google Calendar: {error}",
                    },
                    indent=2,
                )

        return json.dumps(
            {
                "success": True,
                "message": "Reminder updated successfully",
                "reminder": reminder.to_dict(),
            },
            indent=2,
        )

    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def delete_reminder(reminder_id: str) -> str:
    """
    Delete a reminder.

    Args:
        reminder_id: The ID of the reminder to delete

    Returns:
        JSON string with deletion result
    """
    try:
        reminders = _load_reminders()

        if reminder_id not in reminders:
            return json.dumps(
                {
                    "success": False,
                    "error": f"Reminder with ID '{reminder_id}' not found",
                },
                indent=2,
            )

        reminder = reminders[reminder_id]

        # Delete from Google Calendar if synced
        if reminder.calendar_synced and reminder.google_event_id:
            success, error = calendar_integration.delete_event(reminder.google_event_id)
            if not success:
                return json.dumps(
                    {
                        "success": False,
                        "error": f"Failed to delete from Google Calendar: {error}",
                    },
                    indent=2,
                )

        # Delete locally
        del reminders[reminder_id]
        _save_reminders(reminders)

        return json.dumps(
            {
                "success": True,
                "message": f"Reminder '{reminder.event.title}' deleted successfully",
            },
            indent=2,
        )

    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def sync_to_calendar(reminder_id: Optional[str] = None) -> str:
    """
    Sync reminder(s) to Google Calendar.

    Args:
        reminder_id: Specific reminder ID to sync, or None to sync all pending reminders

    Returns:
        JSON string with sync results
    """
    try:
        if not calendar_integration.enabled:
            return json.dumps(
                {
                    "success": False,
                    "error": "Google Calendar integration is not enabled. Set GOOGLE_CALENDAR_ENABLED=true in .env",
                },
                indent=2,
            )

        reminders = _load_reminders()
        results = []

        # Determine which reminders to sync
        to_sync = []
        if reminder_id:
            if reminder_id not in reminders:
                return json.dumps(
                    {
                        "success": False,
                        "error": f"Reminder with ID '{reminder_id}' not found",
                    },
                    indent=2,
                )
            to_sync = [reminders[reminder_id]]
        else:
            # Sync all non-synced, non-cancelled reminders
            to_sync = [
                r
                for r in reminders.values()
                if not r.calendar_synced and r.status != ReminderStatus.CANCELLED
            ]

        # Sync each reminder
        for reminder in to_sync:
            if reminder.calendar_synced:
                # Update existing event
                success, error = calendar_integration.update_event(reminder)
                results.append(
                    {
                        "reminder_id": reminder.id,
                        "title": reminder.event.title,
                        "action": "update",
                        "success": success,
                        "error": error,
                    }
                )
            else:
                # Create new event
                success, event_id, error = calendar_integration.create_event(reminder)
                if success:
                    reminder.calendar_synced = True
                    reminder.google_event_id = event_id
                    reminder.update_timestamp()
                    reminders[reminder.id] = reminder

                results.append(
                    {
                        "reminder_id": reminder.id,
                        "title": reminder.event.title,
                        "action": "create",
                        "success": success,
                        "event_id": event_id,
                        "error": error,
                    }
                )

        # Save changes
        _save_reminders(reminders)

        successful = sum(1 for r in results if r["success"])
        failed = len(results) - successful

        return json.dumps(
            {
                "success": True,
                "synced": successful,
                "failed": failed,
                "results": results,
            },
            indent=2,
        )

    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)


# @mcp.tool()
# def get_current_datetime() -> str:
#     """
#     Get the current date and time.

#     This tool helps you understand what "now" is so you can convert relative time references
#     like "tomorrow", "next week", "in 2 hours" to absolute datetime values.

#     Returns:
#         JSON string with current datetime information
#     """
#     now = datetime.now()

#     return json.dumps(
#         {
#             "success": True,
#             "current_datetime": now.isoformat(),
#             "current_date": now.strftime("%Y-%m-%d"),
#             "current_time": now.strftime("%H:%M:%S"),
#             "day_of_week": now.strftime("%A"),
#             "formatted": now.strftime("%A, %B %d, %Y at %I:%M %p"),
#             "timezone_info": "Local timezone (use this as reference for user's input)",
#         },
#         indent=2,
#     )


@mcp.resource("reminders://all")
def get_all_reminders() -> str:
    """
    Get all reminders.

    Returns markdown formatted list of all reminders.
    """
    reminders = _load_reminders()

    content = "# All Reminders\n\n"
    content += f"Total reminders: {len(reminders)}\n\n"

    if not reminders:
        content += "No reminders found.\n"
        return content

    # Group by status
    by_status = {}
    for reminder in reminders.values():
        status = reminder.status.value
        if status not in by_status:
            by_status[status] = []
        by_status[status].append(reminder)

    # Display each group
    for status in ["pending", "notified", "completed", "cancelled"]:
        if status in by_status:
            content += f"## {status.title()} ({len(by_status[status])})\n\n"
            for reminder in sorted(by_status[status], key=lambda r: r.event.datetime):
                content += _format_reminder_markdown(reminder)
                content += "\n---\n\n"

    return content


@mcp.resource("reminders://upcoming")
def get_upcoming_reminders() -> str:
    """
    Get upcoming reminders (next 7 days).

    Returns markdown formatted list of upcoming reminders.
    """
    reminders = _load_reminders()
    now = datetime.now()
    week_later = now + timedelta(days=7)

    upcoming = [
        r
        for r in reminders.values()
        if now <= r.event.datetime <= week_later
        and r.status in [ReminderStatus.PENDING, ReminderStatus.NOTIFIED]
    ]

    upcoming.sort(key=lambda r: r.event.datetime)

    content = "# Upcoming Reminders (Next 7 Days)\n\n"
    content += f"Found {len(upcoming)} upcoming reminder(s)\n\n"

    if not upcoming:
        content += "No upcoming reminders.\n"
        return content

    for reminder in upcoming:
        content += _format_reminder_markdown(reminder)
        content += "\n---\n\n"

    return content


@mcp.resource("reminders://{date}")
def get_reminders_by_date(date: str) -> str:
    """
    Get reminders for a specific date.

    Args:
        date: Date in YYYY-MM-DD format

    Returns markdown formatted list of reminders for that date.
    """
    try:
        target_date = datetime.fromisoformat(date).date()
        reminders = _load_reminders()

        matching = [
            r for r in reminders.values() if r.event.datetime.date() == target_date
        ]

        matching.sort(key=lambda r: r.event.datetime)

        content = f"# Reminders for {target_date.strftime('%A, %B %d, %Y')}\n\n"
        content += f"Found {len(matching)} reminder(s)\n\n"

        if not matching:
            content += "No reminders for this date.\n"
            return content

        for reminder in matching:
            content += _format_reminder_markdown(reminder)
            content += "\n---\n\n"

        return content

    except ValueError:
        return f"# Error\n\nInvalid date format: {date}. Use YYYY-MM-DD format."


def _format_reminder_markdown(reminder: Reminder) -> str:
    """Format a reminder as markdown."""
    event = reminder.event
    content = f"### {event.title}\n\n"
    content += f"- **ID**: `{reminder.id}`\n"
    content += (
        f"- **Date & Time**: {event.datetime.strftime('%A, %B %d, %Y at %I:%M %p')}\n"
    )
    content += f"- **Status**: {reminder.status.value.title()}\n"

    if event.location:
        content += f"- **Location**: {event.location}\n"

    if event.attendees:
        content += f"- **Attendees**: {', '.join(event.attendees)}\n"

    if reminder.calendar_synced:
        content += "- **Synced to Calendar**: ✓ Yes\n"

    if event.description:
        content += f"\n**Description**: {event.description}\n"

    content += f"\n*Created: {reminder.created_at.strftime('%Y-%m-%d %H:%M')}*\n"

    return content


@mcp.prompt()
def collect_event_details(topic: Optional[str] = None) -> str:
    """Generate a prompt for Claude to collect calendar event details from the user."""
    base_prompt = """You are a helpful and friendly calendar reminder assistant. Your job is to have a natural, conversational interaction with the user to collect all necessary information for creating a calendar event reminder.

## Required Information:
1. **Title** (required): What is the event called?
2. **Date & Time** (required): When is the event? Must be in ISO format (YYYY-MM-DDTHH:MM:SS)

## Optional Information:
3. **Location**: Where is the event taking place?
4. **Attendees**: Who else should be invited? (email addresses)
5. **Description**: Any additional details about the event?
6. **Notification timing**: When should reminders be sent? (default: 1 hour and 1 day before)

## Important Guidelines:

### Date/Time Handling:
- **ALWAYS call get_current_datetime() first** to understand what "now" is
- If user says relative times like "tomorrow", "next week", "in 2 hours", convert them to absolute ISO datetime
- For "tomorrow at 3pm" → add 1 day to current date and set time to 15:00:00
- For "next Friday" → calculate the date of next Friday
- For times without date → assume they mean today if time is in future, otherwise tomorrow
- Always confirm the calculated datetime with user in friendly format before creating

### Conversation Flow:
1. First, call get_current_datetime() to know what "now" is
2. Ask questions naturally, one or two at a time - don't overwhelm the user
3. If the user provides partial information, acknowledge what you got and ask for what's missing
4. Be friendly, conversational, and helpful
5. Confirm all details before creating the reminder
6. Once you have title and datetime, create the reminder immediately
7. After successful creation, ask if they want to sync to Google Calendar

### Examples of Good Interaction:
- User: "Team meeting tomorrow at 2pm"
- You: *calls get_current_datetime()* "Got it! I'll create a reminder for your team meeting tomorrow (Tuesday, January 5) at 2:00 PM. Would you like to add a location or any attendees?"

- User: "Doctor appointment next week"
- You: "I'd be happy to help! *calls get_current_datetime()* Which day next week is your doctor appointment, and what time?"

### Creating the Reminder:
- Once you have title and datetime, use create_reminder() immediately
- You can create with just title and datetime, then update later if user provides more info
- Always show the user what was created and offer to add more details or sync to calendar

### After Creation:
- Confirm the reminder was created successfully
- Mention when notifications will be sent
- Ask if they want to sync to Google Calendar (if not already mentioned)
- Ask if they want to add or modify anything

"""

    if topic:
        base_prompt += f"\n\n## User's Initial Request:\nThe user wants to create a reminder about: '{topic}'\n\nStart by calling get_current_datetime(), then acknowledge their request warmly and ask for the specific date/time and any other missing details."
    else:
        base_prompt += "\n\n## Starting the Conversation:\nCall get_current_datetime() first, then warmly greet the user and ask what event they would like to create a reminder for."

    return base_prompt


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport="stdio")
