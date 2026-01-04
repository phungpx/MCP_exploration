from datetime import datetime as dt
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr, field_validator
from enum import Enum
import uuid


class ReminderStatus(str, Enum):
    """Status of a reminder."""

    PENDING = "pending"
    NOTIFIED = "notified"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class NotificationSettings(BaseModel):
    """Settings for when to send notifications."""

    minutes_before: List[int] = Field(
        default=[60, 1440],  # 1 hour and 1 day before
        description="Minutes before event to send notifications",
    )
    email_enabled: bool = Field(
        default=True, description="Whether to send email notifications"
    )


class EventDetails(BaseModel):
    """Details of a calendar event."""

    title: str = Field(..., min_length=1, description="Event title")
    datetime: dt = Field(..., description="Event date and time")
    attendees: List[EmailStr] = Field(
        default_factory=list, description="List of attendee email addresses"
    )
    location: Optional[str] = Field(None, description="Event location")
    description: Optional[str] = Field(None, description="Event description")

    @field_validator("datetime")
    @classmethod
    def validate_future_datetime(cls, v: dt) -> dt:
        """Ensure the datetime is in the future."""
        if v < dt.now():
            raise ValueError("Event datetime must be in the future")
        return v


class Reminder(BaseModel):
    """Complete reminder model with metadata."""

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), description="Unique reminder ID"
    )
    event: EventDetails = Field(..., description="Event details")
    notification_settings: NotificationSettings = Field(
        default_factory=NotificationSettings, description="Notification settings"
    )
    status: ReminderStatus = Field(
        default=ReminderStatus.PENDING, description="Reminder status"
    )
    calendar_synced: bool = Field(
        default=False, description="Whether synced to Google Calendar"
    )
    google_event_id: Optional[str] = Field(
        None, description="Google Calendar event ID if synced"
    )
    created_at: dt = Field(default_factory=dt.now, description="Creation timestamp")
    updated_at: dt = Field(default_factory=dt.now, description="Last update timestamp")

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = dt.now()

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "event": {
                "title": self.event.title,
                "datetime": self.event.datetime.isoformat(),
                "attendees": self.event.attendees,
                "location": self.event.location,
                "description": self.event.description,
            },
            "notification_settings": {
                "minutes_before": self.notification_settings.minutes_before,
                "email_enabled": self.notification_settings.email_enabled,
            },
            "status": self.status.value,
            "calendar_synced": self.calendar_synced,
            "google_event_id": self.google_event_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Reminder":
        """Create Reminder from dictionary."""
        event_data = data["event"]
        event_data["datetime"] = dt.fromisoformat(event_data["datetime"])

        return cls(
            id=data["id"],
            event=EventDetails(**event_data),
            notification_settings=NotificationSettings(
                **data.get("notification_settings", {})
            ),
            status=ReminderStatus(data.get("status", "pending")),
            calendar_synced=data.get("calendar_synced", False),
            google_event_id=data.get("google_event_id"),
            created_at=dt.fromisoformat(data["created_at"]),
            updated_at=dt.fromisoformat(data["updated_at"]),
        )


class NotificationLog(BaseModel):
    """Log entry for sent notifications."""

    reminder_id: str
    notification_time: dt
    minutes_before: int
    sent_at: dt = Field(default_factory=dt.now)
    success: bool = Field(default=True)
    error_message: Optional[str] = Field(None)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "reminder_id": self.reminder_id,
            "notification_time": self.notification_time.isoformat(),
            "minutes_before": self.minutes_before,
            "sent_at": self.sent_at.isoformat(),
            "success": self.success,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NotificationLog":
        """Create NotificationLog from dictionary."""
        return cls(
            reminder_id=data["reminder_id"],
            notification_time=dt.fromisoformat(data["notification_time"]),
            minutes_before=data["minutes_before"],
            sent_at=dt.fromisoformat(data["sent_at"]),
            success=data.get("success", True),
            error_message=data.get("error_message"),
        )
