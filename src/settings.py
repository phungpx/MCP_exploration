import os
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


class LangfuseSettings(ProjectBaseSettings):
    langfuse_secret_key: str | None = None
    langfuse_public_key: str | None = None
    langfuse_base_url: str | None = None


class ProjectSettings(LLMSettings, LangfuseSettings):
    research_dir: str = "src/papers"

    @property
    def llm(self) -> LLMSettings:
        return LLMSettings(**self.model_dump())

    @property
    def langfuse(self) -> LangfuseSettings:
        return LangfuseSettings(**self.model_dump())


settings = ProjectSettings()
os.environ["LANGFUSE_PUBLIC_KEY"] = settings.langfuse.langfuse_public_key
os.environ["LANGFUSE_SECRET_KEY"] = settings.langfuse.langfuse_secret_key
os.environ["LANGFUSE_BASE_URL"] = settings.langfuse.langfuse_base_url
