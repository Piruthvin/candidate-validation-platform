from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="Candidate Validation Platform", alias="APP_NAME")
    app_version: str = Field(default="2.0.0", alias="APP_VERSION")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    azure_storage_connection_string: str | None = Field(default=None, alias="AZURE_STORAGE_CONNECTION_STRING")
    azure_storage_container_name: str = Field(default="candidate-reports", alias="AZURE_STORAGE_CONTAINER_NAME")
    azure_storage_account_name: str | None = Field(default=None, alias="AZURE_STORAGE_ACCOUNT_NAME")
    azure_storage_account_key: str | None = Field(default=None, alias="AZURE_STORAGE_ACCOUNT_KEY")
    azure_sas_expiry_hours: int = Field(default=24, alias="AZURE_SAS_EXPIRY_HOURS")

    zoho_client_id: str | None = Field(default=None, alias="ZOHO_CLIENT_ID")
    zoho_client_secret: str | None = Field(default=None, alias="ZOHO_CLIENT_SECRET")
    zoho_refresh_token: str | None = Field(default=None, alias="ZOHO_REFRESH_TOKEN")
    zoho_accounts_url: str = Field(default="https://accounts.zoho.in", alias="ZOHO_ACCOUNTS_URL")
    zoho_api_base_url: str = Field(default="https://recruit.zoho.in/recruit/v2", alias="ZOHO_API_BASE_URL")

    company_request_timeout: int = Field(default=10, alias="COMPANY_REQUEST_TIMEOUT")

    linkedin_timeout: int = Field(default=5, alias="LINKEDIN_TIMEOUT")

    cors_origins: list[str] = Field(default=["*"], alias="CORS_ORIGINS")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if value is None:
            return ["*"]

        if isinstance(value, list):
            return value

        if isinstance(value, str):
            value = value.strip()

            if value == "*":
                return ["*"]

            return [origin.strip() for origin in value.split(",") if origin.strip()]

        return value