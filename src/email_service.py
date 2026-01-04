import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from src.models import Reminder
from src.settings import settings


class EmailService:
    """Service for sending email notifications."""

    def __init__(self):
        self.smtp_server = settings.smtp_server
        self.smtp_port = settings.smtp_port
        self.from_email = settings.email_from
        self.password = settings.email_password
        self.use_tls = settings.email_use_tls
        self.enabled = settings.email_enabled

    def send_reminder_notification(
        self, reminder: Reminder, recipients: List[str], minutes_before: int
    ) -> tuple[bool, Optional[str]]:
        """
        Send a reminder notification email.

        Args:
            reminder: The reminder to send notification for
            recipients: List of email addresses to send to
            minutes_before: How many minutes before the event this notification is

        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        if not self.enabled:
            return False, "Email notifications are disabled in settings"

        if not self.from_email or not self.password:
            return False, "Email credentials not configured"

        if not recipients:
            recipients = [self.from_email]  # Send to self if no recipients

        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"Reminder: {reminder.event.title}"
            msg["From"] = self.from_email
            msg["To"] = ", ".join(recipients)

            # Create email body
            time_text = self._format_time_until(minutes_before)
            text_body = self._create_text_body(reminder, time_text)
            html_body = self._create_html_body(reminder, time_text)

            # Attach both plain text and HTML versions
            part1 = MIMEText(text_body, "plain")
            part2 = MIMEText(html_body, "html")
            msg.attach(part1)
            msg.attach(part2)

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.from_email, self.password)
                server.send_message(msg)

            return True, None

        except Exception as e:
            return False, str(e)

    def _format_time_until(self, minutes: int) -> str:
        """Format minutes into a human-readable string."""
        if minutes < 60:
            return f"{minutes} minutes"
        elif minutes < 1440:
            hours = minutes // 60
            return f"{hours} hour{'s' if hours != 1 else ''}"
        else:
            days = minutes // 1440
            return f"{days} day{'s' if days != 1 else ''}"

    def _create_text_body(self, reminder: Reminder, time_text: str) -> str:
        """Create plain text email body."""
        event = reminder.event
        body = f"""
Reminder: {event.title}

This is a reminder for your upcoming event in {time_text}.

Event Details:
--------------
Title: {event.title}
Date & Time: {event.datetime.strftime('%A, %B %d, %Y at %I:%M %p')}
"""

        if event.location:
            body += f"Location: {event.location}\n"

        if event.attendees:
            body += f"Attendees: {', '.join(event.attendees)}\n"

        if event.description:
            body += f"\nDescription:\n{event.description}\n"

        body += """
--------------
This is an automated reminder from your Calendar Reminder Agent.
"""
        return body

    def _create_html_body(self, reminder: Reminder, time_text: str) -> str:
        """Create HTML email body."""
        event = reminder.event
        html = f"""
<html>
  <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
      <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
        Reminder: {event.title}
      </h2>
      
      <p style="font-size: 16px; color: #e74c3c;">
        <strong>⏰ This is a reminder for your upcoming event in {time_text}.</strong>
      </p>
      
      <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
        <h3 style="margin-top: 0; color: #2c3e50;">Event Details</h3>
        
        <p><strong>📅 Title:</strong> {event.title}</p>
        <p><strong>🕐 Date & Time:</strong> {event.datetime.strftime('%A, %B %d, %Y at %I:%M %p')}</p>
"""

        if event.location:
            html += f"        <p><strong>📍 Location:</strong> {event.location}</p>\n"

        if event.attendees:
            html += f'        <p><strong>👥 Attendees:</strong> {", ".join(event.attendees)}</p>\n'

        if event.description:
            html += f"""
        <p><strong>📝 Description:</strong></p>
        <p style="margin-left: 20px;">{event.description}</p>
"""

        html += """
      </div>
      
      <p style="font-size: 12px; color: #7f8c8d; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
        This is an automated reminder from your Calendar Reminder Agent.
      </p>
    </div>
  </body>
</html>
"""
        return html

    def test_connection(self) -> tuple[bool, Optional[str]]:
        """Test SMTP connection and credentials."""
        if not self.enabled:
            return False, "Email notifications are disabled"

        if not self.from_email or not self.password:
            return False, "Email credentials not configured"

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.from_email, self.password)
            return True, None
        except Exception as e:
            return False, str(e)
