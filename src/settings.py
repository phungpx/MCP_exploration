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


class ProjectSettings(LLMSettings):
    research_dir: str = "src/papers"

    @property
    def llm(self) -> LLMSettings:
        return LLMSettings(**self.model_dump())


settings = ProjectSettings()
