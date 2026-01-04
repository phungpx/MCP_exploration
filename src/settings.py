from abc import ABC
from pydantic_settings import BaseSettings, SettingsConfigDict


class ProjectBaseSettings(BaseSettings, ABC):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class LLMSettings(ProjectBaseSettings):
    llm_model: str = "gpt-4o-mini"
    llm_api_key: str | None = None
    llm_base_url: str | None = None
    llm_temperature: float = 0.0
    llm_max_tokens: int = 16384


class GoogleCalendarSettings(ProjectBaseSettings):
    google_calendar_enabled: bool = False
    google_credentials_path: str = "./credentials.json"
    google_token_path: str = "./token.json"
    google_calendar_id: str = "primary"


class EmailSettings(ProjectBaseSettings):
    email_enabled: bool = False
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    email_from: str | None = None
    email_password: str | None = None
    email_use_tls: bool = True


class ProjectSettings(LLMSettings, GoogleCalendarSettings, EmailSettings):
    save_dir: str = "reminders"

    @property
    def llm(self) -> LLMSettings:
        return LLMSettings(**self.model_dump())

    @property
    def google_calendar(self) -> GoogleCalendarSettings:
        return GoogleCalendarSettings(**self.model_dump())

    @property
    def email(self) -> EmailSettings:
        return EmailSettings(**self.model_dump())


settings = ProjectSettings()
