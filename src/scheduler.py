import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src.models import Reminder, NotificationLog, ReminderStatus
from src.email_service import EmailService
from src.settings import settings


class ReminderScheduler:
    """Background scheduler for sending reminder notifications."""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.email_service = EmailService()
        self.reminder_dir = settings.save_dir
        self.notification_log_file = os.path.join(
            self.reminder_dir, "notification_log.json"
        )

        # Create directory if needed
        os.makedirs(self.reminder_dir, exist_ok=True)

    def start(self, check_interval_minutes: int = 5) -> None:
        """
        Start the scheduler.

        Args:
            check_interval_minutes: How often to check for reminders to send (default: 5 minutes)
        """
        # Schedule the reminder check job
        self.scheduler.add_job(
            func=self.check_and_send_reminders,
            trigger=IntervalTrigger(minutes=check_interval_minutes),
            id="reminder_check",
            name="Check and send reminder notifications",
            replace_existing=True,
        )

        self.scheduler.start()
        print(
            f"Reminder scheduler started. Checking every {check_interval_minutes} minutes."
        )

    def stop(self) -> None:
        """Stop the scheduler."""
        self.scheduler.shutdown()
        print("Reminder scheduler stopped.")

    def check_and_send_reminders(self) -> None:
        """Check for reminders that need notifications and send them."""
        try:
            reminders = self._load_reminders()
            notification_log = self._load_notification_log()
            now = datetime.now()

            sent_count = 0

            for reminder in reminders.values():
                # Skip non-pending reminders
                if reminder.status not in [
                    ReminderStatus.PENDING,
                    ReminderStatus.NOTIFIED,
                ]:
                    continue

                # Skip past events
                if reminder.event.datetime < now:
                    continue

                # Check if email notifications are enabled
                if not reminder.notification_settings.email_enabled:
                    continue

                # Check each notification time
                for minutes_before in reminder.notification_settings.minutes_before:
                    notification_time = reminder.event.datetime - timedelta(
                        minutes=minutes_before
                    )

                    # Check if it's time to send this notification
                    if now >= notification_time:
                        # Check if we've already sent this notification
                        log_key = f"{reminder.id}_{minutes_before}"
                        if log_key in notification_log:
                            continue

                        # Send notification
                        recipients = (
                            [settings.email_from] if settings.email_from else []
                        )
                        if reminder.event.attendees:
                            recipients.extend(reminder.event.attendees)

                        success, error = self.email_service.send_reminder_notification(
                            reminder=reminder,
                            recipients=list(set(recipients)),  # Remove duplicates
                            minutes_before=minutes_before,
                        )

                        # Log the notification attempt
                        log_entry = NotificationLog(
                            reminder_id=reminder.id,
                            notification_time=notification_time,
                            minutes_before=minutes_before,
                            success=success,
                            error_message=error,
                        )
                        notification_log[log_key] = log_entry

                        if success:
                            sent_count += 1
                            print(
                                f"Sent notification for '{reminder.event.title}' ({minutes_before} min before)"
                            )

                            # Update reminder status
                            if reminder.status == ReminderStatus.PENDING:
                                reminder.status = ReminderStatus.NOTIFIED
                                reminders[reminder.id] = reminder
                        else:
                            print(
                                f"Failed to send notification for '{reminder.event.title}': {error}"
                            )

            # Save updated data
            if sent_count > 0:
                self._save_reminders(reminders)
            self._save_notification_log(notification_log)

            if sent_count > 0:
                print(f"Sent {sent_count} notification(s)")

        except Exception as e:
            print(f"Error in scheduler: {e}")

    def _load_reminders(self) -> Dict[str, Reminder]:
        """Load reminders from storage."""
        file_path = os.path.join(self.reminder_dir, "reminders.json")
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                return {id: Reminder.from_dict(r) for id, r in data.items()}
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_reminders(self, reminders: Dict[str, Reminder]) -> None:
        """Save reminders to storage."""
        file_path = os.path.join(self.reminder_dir, "reminders.json")
        data = {id: r.to_dict() for id, r in reminders.items()}
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

    def _load_notification_log(self) -> Dict[str, NotificationLog]:
        """Load notification log from storage."""
        try:
            with open(self.notification_log_file, "r") as f:
                data = json.load(f)
                return {
                    key: NotificationLog.from_dict(entry) for key, entry in data.items()
                }
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_notification_log(self, log: Dict[str, NotificationLog]) -> None:
        """Save notification log to storage."""
        data = {key: entry.to_dict() for key, entry in log.items()}
        with open(self.notification_log_file, "w") as f:
            json.dump(data, f, indent=2)

    def get_pending_notifications(self) -> List[dict]:
        """Get a list of pending notifications."""
        reminders = self._load_reminders()
        notification_log = self._load_notification_log()
        now = datetime.now()

        pending = []

        for reminder in reminders.values():
            if reminder.status not in [ReminderStatus.PENDING, ReminderStatus.NOTIFIED]:
                continue

            if reminder.event.datetime < now:
                continue

            for minutes_before in reminder.notification_settings.minutes_before:
                notification_time = reminder.event.datetime - timedelta(
                    minutes=minutes_before
                )
                log_key = f"{reminder.id}_{minutes_before}"

                if log_key not in notification_log:
                    pending.append(
                        {
                            "reminder_id": reminder.id,
                            "title": reminder.event.title,
                            "event_datetime": reminder.event.datetime.isoformat(),
                            "notification_time": notification_time.isoformat(),
                            "minutes_before": minutes_before,
                            "is_due": now >= notification_time,
                        }
                    )

        return sorted(pending, key=lambda x: x["notification_time"])


def main():
    """Run the scheduler as a standalone service."""
    scheduler = ReminderScheduler()

    print("=" * 60)
    print("Calendar Reminder Notification Service")
    print("=" * 60)

    # Test email configuration
    if settings.email_enabled:
        print("\nTesting email configuration...")
        success, error = scheduler.email_service.test_connection()
        if success:
            print("✓ Email service connected successfully")
        else:
            print(f"✗ Email service error: {error}")
            print("  Notifications will not be sent!")
    else:
        print("\n⚠ Email notifications are disabled in settings")

    # Show pending notifications
    pending = scheduler.get_pending_notifications()
    if pending:
        print(f"\n{len(pending)} pending notification(s):")
        for notif in pending[:5]:  # Show first 5
            status = "DUE NOW" if notif["is_due"] else "scheduled"
            print(
                f"  - {notif['title']} ({notif['minutes_before']}min before) - {status}"
            )
        if len(pending) > 5:
            print(f"  ... and {len(pending) - 5} more")
    else:
        print("\nNo pending notifications")

    print("\nStarting scheduler...")
    scheduler.start()

    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        print("\nShutting down scheduler...")
        scheduler.stop()
        print("Goodbye!")


if __name__ == "__main__":
    main()
