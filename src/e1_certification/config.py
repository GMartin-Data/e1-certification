"""
Configuration management using pydantic-settings.
Handles environment variables and validation.
"""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ENVIRONMENTS = ["dev", "prod"]
LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    """Application settings with validation."""

    # Environment
    environment: str = Field(default="dev", description="Deployment environment")
    log_level: str = Field(default="INFO", description="Logging level")

    # AWS Configuration
    aws_region: str = Field(default="eu-west-3", description="AWS region")
    aws_profile: str | None = Field(default=None, description="AWS profile name")
    s3_bucket_name: str | None = Field(
        default=None, description="S3 bucket for Excel files"
    )

    # Database configuration
    db_host: str | None = Field(default=None, description="Database host")
    db_port: int = Field(default=3306, description="Database port")
    db_name: str = Field(default="e1_certification", description="Database name")
    db_user: str | None = Field(default=None, description="Database username")
    db_password: str | None = Field(default=None, description="Database password")
    db_password_param: str | None = Field(
        default=None, description="SSM parameter for database password"
    )

    # API Configuration
    api_key: str | None = Field(default=None, description="API key for authentication")
    jwt_secret_key: str = Field(
        default="dev-secret-key-change-in-production", description="JWT secret key"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiration_minutes: int = Field(default=30, description="JWT token expiration")

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment is either dev or prod."""
        if v not in ENVIRONMENTS:
            raise ValueError("Environment must be 'dev' or 'prod'")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_levels(cls, v: str) -> str:
        """Check whether log level is valid."""
        if v.upper() not in LOG_LEVELS:
            raise ValueError(f"Log level must be one of {LOG_LEVELS}")
        return v

    @property
    def database_password(self) -> str | None:
        """
        Get database password from environment or SSM.

        In Lambda: Fetches from SSM Parameter Store
        Locally: Uses DB_PASSWORD from .env
        """
        # If running in Lamba with SSM parameter name
        if self.db_password_param:
            try:
                import boto3

                ssm = boto3.client("ssm", region_name=self.aws_region)
                response = ssm.get_parameter(
                    Name=self.db_password_param, WithDecryption=True
                )
                return response["Parameter"]["Value"]
            except Exception as e:
                print(f"❌ Failed to fetch password from SSM: {e}")
                return None

        # Otherwise use local environment variable
        return self.db_password

    @property
    def database_url(self) -> str | None:
        """Construct database URL for SQLAlchemy."""
        password = self.database_password
        if not all([self.db_host, self.db_user, password]):
            return None
        else:
            return (
                f"mysql+pymysql://{self.db_user}:{password}"
                f"@{self.db_host}:{self.db_port}/{self.db_name}"
            )

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "prod"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "dev"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Settings instance (cached for performance)
    """
    return Settings()


# Create a convenience instance
settings = get_settings()
