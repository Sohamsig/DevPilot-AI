from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str
    model_name: str = "gpt-4.1-mini"
    workspace_root: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()