from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")

    allowed_origins: str = Field(default="*", alias="ALLOWED_ORIGINS")

    default_days: int = Field(default=7, alias="DEFAULT_DAYS")
    max_links_per_day: int = Field(default=2, alias="MAX_LINKS_PER_DAY")
    max_total_links: int = Field(default=10, alias="MAX_TOTAL_LINKS")

    max_tool_calls: int = Field(default=8, alias="MAX_TOOL_CALLS")
    enable_fetch_tool: bool = Field(default=True, alias="ENABLE_FETCH_TOOL")

settings = Settings()
