import os
import json
from datetime import datetime, timedelta
from typing import Optional, List
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.models import Reminder
from src.settings import settings


# If modifying these scopes, delete the token.json file
SCOPES = ["https://www.googleapis.com/auth/calendar"]


class GoogleCalendarIntegration:
    """Integration with Google Calendar API."""

    def __init__(self):
        self.enabled = settings.google_calendar_enabled
        self.credentials_path = settings.google_credentials_path
        self.token_path = settings.google_token_path
        self.calendar_id = settings.google_calendar_id
        self.service = None

        if self.enabled:
            self._authenticate()

    def _authenticate(self) -> None:
        """Authenticate with Google Calendar API using OAuth2."""
        creds = None

        # Load existing token if available
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)

        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(
                        f"Credentials file not found: {self.credentials_path}\n"
                        "Please download credentials.json from Google Cloud Console"
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save credentials for next run
            with open(self.token_path, "w") as token:
                token.write(creds.to_json())

        self.service = build("calendar", "v3", credentials=creds)

    def create_event(
        self, reminder: Reminder
    ) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Create a calendar event from a reminder.

        Args:
            reminder: The reminder to create an event for

        Returns:
            Tuple of (success: bool, event_id: Optional[str], error: Optional[str])
        """
        if not self.enabled or not self.service:
            return False, None, "Google Calendar integration is not enabled"

        try:
            event = self._reminder_to_event(reminder)
            result = (
                self.service.events()
                .insert(calendarId=self.calendar_id, body=event)
                .execute()
            )

            event_id = result.get("id")
            return True, event_id, None

        except HttpError as e:
            return False, None, f"Google Calendar API error: {str(e)}"
        except Exception as e:
            return False, None, str(e)

    def update_event(self, reminder: Reminder) -> tuple[bool, Optional[str]]:
        """
        Update an existing calendar event.

        Args:
            reminder: The reminder with updated information

        Returns:
            Tuple of (success: bool, error: Optional[str])
        """
        if not self.enabled or not self.service:
            return False, "Google Calendar integration is not enabled"

        if not reminder.google_event_id:
            return False, "Reminder is not synced with Google Calendar"

        try:
            event = self._reminder_to_event(reminder)
            self.service.events().update(
                calendarId=self.calendar_id,
                eventId=reminder.google_event_id,
                body=event,
            ).execute()

            return True, None

        except HttpError as e:
            return False, f"Google Calendar API error: {str(e)}"
        except Exception as e:
            return False, str(e)

    def delete_event(self, event_id: str) -> tuple[bool, Optional[str]]:
        """
        Delete a calendar event.

        Args:
            event_id: The Google Calendar event ID

        Returns:
            Tuple of (success: bool, error: Optional[str])
        """
        if not self.enabled or not self.service:
            return False, "Google Calendar integration is not enabled"

        try:
            self.service.events().delete(
                calendarId=self.calendar_id, eventId=event_id
            ).execute()

            return True, None

        except HttpError as e:
            return False, f"Google Calendar API error: {str(e)}"
        except Exception as e:
            return False, str(e)

    def get_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        max_results: int = 100,
    ) -> tuple[bool, List[dict], Optional[str]]:
        """
        Get calendar events within a date range.

        Args:
            start_date: Start of date range (defaults to now)
            end_date: End of date range (defaults to 30 days from now)
            max_results: Maximum number of events to retrieve

        Returns:
            Tuple of (success: bool, events: List[dict], error: Optional[str])
        """
        if not self.enabled or not self.service:
            return False, [], "Google Calendar integration is not enabled"

        try:
            if not start_date:
                start_date = datetime.now()
            if not end_date:
                end_date = start_date + timedelta(days=30)

            events_result = (
                self.service.events()
                .list(
                    calendarId=self.calendar_id,
                    timeMin=start_date.isoformat() + "Z",
                    timeMax=end_date.isoformat() + "Z",
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            events = events_result.get("items", [])
            return True, events, None

        except HttpError as e:
            return False, [], f"Google Calendar API error: {str(e)}"
        except Exception as e:
            return False, [], str(e)

    def _reminder_to_event(self, reminder: Reminder) -> dict:
        """Convert a Reminder to Google Calendar event format."""
        event = reminder.event

        # Calculate end time (default 1 hour duration)
        end_time = event.datetime + timedelta(hours=1)

        calendar_event = {
            "summary": event.title,
            "start": {
                "dateTime": event.datetime.isoformat(),
                "timeZone": "UTC",
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": "UTC",
            },
        }

        if event.location:
            calendar_event["location"] = event.location

        if event.description:
            calendar_event["description"] = event.description

        if event.attendees:
            calendar_event["attendees"] = [
                {"email": email} for email in event.attendees
            ]

        # Add reminders based on notification settings
        if reminder.notification_settings.minutes_before:
            calendar_event["reminders"] = {
                "useDefault": False,
                "overrides": [
                    {"method": "email", "minutes": minutes}
                    for minutes in reminder.notification_settings.minutes_before
                ],
            }

        return calendar_event

    def test_connection(self) -> tuple[bool, Optional[str]]:
        """Test connection to Google Calendar API."""
        if not self.enabled:
            return False, "Google Calendar integration is disabled"

        try:
            if not self.service:
                self._authenticate()

            # Try to list calendars as a test
            self.service.calendarList().list(maxResults=1).execute()
            return True, None

        except Exception as e:
            return False, str(e)
