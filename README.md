# Calendar Reminder Agent with MCP

A conversational calendar reminder agent that uses the Model Context Protocol (MCP) to help users create, manage, and sync calendar reminders. The agent can store reminders locally, sync them to Google Calendar, and send email notifications.

## Features

- 🤖 **Conversational Interface**: Natural language interaction to create and manage reminders
- 📅 **Google Calendar Integration**: Optional sync with Google Calendar
- 📧 **Email Notifications**: Automated email reminders before events
- 🔄 **MCP Architecture**: Clean server-client separation using Model Context Protocol
- 💾 **Local Storage**: JSON-based reminder storage with full CRUD operations
- ⏰ **Background Scheduler**: Automatic notification delivery

## Architecture

```
User ←→ MCP Client ←→ MCP Server ←→ Local Storage (JSON)
                            ↓
                    Google Calendar API
                            ↓
                    Email Scheduler → SMTP
```

## Installation

### Prerequisites

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) package manager
- OpenAI API key (or compatible LLM endpoint)
- Google Cloud Project (for Calendar integration)
- SMTP email account (for notifications)

### Setup

1. **Clone and install dependencies:**

```bash
cd MCP_exploration
uv sync
```

2. **Create .env file:**

Create a `.env` file in the project root with the following configuration:

```env
# LLM Configuration (Required)
LLM_MODEL=gpt-4o-mini
LLM_API_KEY=your_openai_api_key_here
LLM_BASE_URL=https://api.openai.com/v1
LLM_TEMPERATURE=0.0
LLM_MAX_TOKENS=16384

# Google Calendar (Optional)
GOOGLE_CALENDAR_ENABLED=false
GOOGLE_CREDENTIALS_PATH=./credentials.json
GOOGLE_TOKEN_PATH=./token.json
GOOGLE_CALENDAR_ID=primary

# Email Notifications (Optional)
EMAIL_ENABLED=false
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_FROM=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_USE_TLS=true

# Storage
SAVE_DIR=reminders
```

3. **Setup Google Calendar (Optional):**

If you want Google Calendar integration:

a. Go to [Google Cloud Console](https://console.cloud.google.com/)
b. Create a new project or select an existing one
c. Enable the Google Calendar API
d. Create OAuth 2.0 credentials (Desktop app)
e. Download the credentials JSON file and save as `credentials.json` in the project root
f. Set `GOOGLE_CALENDAR_ENABLED=true` in `.env`

4. **Setup Email Notifications (Optional):**

For Gmail:
a. Enable 2-factor authentication on your Google account
b. Generate an [App Password](https://myaccount.google.com/apppasswords)
c. Use the app password in the `EMAIL_PASSWORD` field
d. Set `EMAIL_ENABLED=true` in `.env`

For other providers, adjust `SMTP_SERVER` and `SMTP_PORT` accordingly.

## Usage

### Running the Chatbot

Start the conversational reminder agent:

```bash
uv run python -m src.client
```

### Commands

- `@all` - View all reminders
- `@upcoming` - View upcoming reminders (next 7 days)
- `@YYYY-MM-DD` - View reminders for a specific date (e.g., `@2024-12-25`)
- `/prompts` - List available prompts
- `/prompt <name> <args>` - Execute a specific prompt
- `quit` - Exit the application

### Example Conversations

**Creating a reminder:**
```
Query: Create a reminder for team standup tomorrow at 10am
```

**Listing reminders:**
```
Query: Show me my reminders for next week
```

**Syncing to Google Calendar:**
```
Query: Sync all my reminders to Google Calendar
```

**Updating a reminder:**
```
Query: Update the team standup reminder to include john@example.com
```

### Running the Email Scheduler

To enable automatic email notifications, run the scheduler in a separate terminal:

```bash
uv run python -m src.scheduler
```

The scheduler will:
- Check for pending reminders every 5 minutes
- Send email notifications at the configured times before events
- Log all notification attempts

### MCP Server Tools

The following tools are available through the MCP server:

1. **create_reminder** - Create a new reminder
   - `title`: Event title (required)
   - `datetime_str`: ISO format datetime (required)
   - `attendees`: List of email addresses (optional)
   - `location`: Event location (optional)
   - `description`: Event description (optional)
   - `notification_minutes`: List of minutes before event (optional)

2. **get_reminder** - Get details of a specific reminder
   - `reminder_id`: The reminder ID

3. **list_reminders** - List reminders with optional filters
   - `start_date`: Filter by start date (optional)
   - `end_date`: Filter by end date (optional)
   - `status`: Filter by status (optional)

4. **update_reminder** - Update an existing reminder
   - `reminder_id`: The reminder ID (required)
   - All other fields optional

5. **delete_reminder** - Delete a reminder
   - `reminder_id`: The reminder ID

6. **sync_to_calendar** - Sync to Google Calendar
   - `reminder_id`: Specific reminder or None for all (optional)

### MCP Resources

- `reminders://all` - All reminders
- `reminders://upcoming` - Upcoming reminders (next 7 days)
- `reminders://{date}` - Reminders for a specific date (YYYY-MM-DD)

### MCP Prompts

- `collect_event_details` - Interactive prompt to collect all event information

## Project Structure

```
MCP_exploration/
├── src/
│   ├── client.py              # MCP client with conversational interface
│   ├── server.py              # MCP server with reminder tools
│   ├── models.py              # Pydantic data models
│   ├── settings.py            # Configuration management
│   ├── calendar_integration.py # Google Calendar API wrapper
│   ├── email_service.py       # Email notification service
│   └── scheduler.py           # Background notification scheduler
├── reminders/                 # Reminder storage (auto-created)
│   ├── reminders.json         # Main reminder database
│   └── notification_log.json  # Notification history
├── pyproject.toml            # Project dependencies
├── .env                      # Configuration (create from .env.example)
└── README.md                 # This file
```

## Data Models

### Reminder
```json
{
  "id": "uuid",
  "event": {
    "title": "Team Meeting",
    "datetime": "2024-12-25T14:30:00",
    "attendees": ["user@example.com"],
    "location": "Conference Room A",
    "description": "Weekly sync"
  },
  "notification_settings": {
    "minutes_before": [60, 1440],
    "email_enabled": true
  },
  "status": "pending",
  "calendar_synced": false,
  "google_event_id": null,
  "created_at": "2024-01-04T10:00:00",
  "updated_at": "2024-01-04T10:00:00"
}
```

## Troubleshooting

### Google Calendar Authentication

On first use with Google Calendar enabled, a browser window will open for OAuth authentication. After granting permissions, a `token.json` file will be created for future use.

### Email Notifications Not Sending

1. Check that `EMAIL_ENABLED=true` in `.env`
2. Verify SMTP credentials are correct
3. For Gmail, ensure you're using an App Password, not your regular password
4. Check the scheduler logs for specific error messages

### MCP Connection Issues

If the client can't connect to the server:
1. Ensure `uv` is installed and in your PATH
2. Check that all dependencies are installed (`uv sync`)
3. Verify Python 3.13+ is available

## Development

### Running Tests

```bash
# Check linting
uv run ruff check .

# Format code
uv run ruff format .
```

### Adding New Features

The MCP architecture makes it easy to extend:
- Add new tools in `src/server.py` using the `@mcp.tool()` decorator
- Add new resources using `@mcp.resource()` decorator
- Add new prompts using `@mcp.prompt()` decorator

## License

This project is for educational and personal use.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.
