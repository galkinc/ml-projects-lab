from typing import Any, Dict, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BedrockConfig(BaseSettings):
    model_id: str = Field("us.amazon.nova-micro-v1:0", alias="BEDROCK_MODEL_ID")
    temperature: float = Field(0.1, alias="BEDROCK_TEMPERATURE")
    temp_strategy_a: float = Field(0.1, alias="TEMP_STRATEGY_A")
    temp_strategy_b: float = Field(0.1, alias="TEMP_STRATEGY_B")
    temp_strategy_c_base: float = Field(0.1, alias="TEMP_STRATEGY_C_BASE")
    temp_strategy_c_retry: float = Field(0.2, alias="TEMP_STRATEGY_C_RETRY")
    min_words: int = Field(5, alias="MIN_WORDS")
    max_words: int = Field(12, alias="MAX_WORDS")
    max_tokens: int = Field(30, alias="MAX_TOKENS")
    max_attempts: int = Field(2, alias="MAX_ATTEMPTS")


class Settings(BaseSettings):
    aws_access_key_id: Optional[str] = Field(None, alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(None, alias="AWS_SECRET_ACCESS_KEY")
    aws_region: str = Field("us-east-1", alias="AWS_REGION")

    logging_level: str = Field(
        default="DEBUG", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"
    )
    logging_format: str = Field(
        default="%(asctime)s UTC - %(levelname)s - %(message)s",
        description="Log message format with UTC timezone",
    )
    boto3_debug_logging: bool = Field(
        False, description="True if you want to see boto3 dubuging info."
    )
    asyncio_debug_logging: bool = Field(
        False, description="True if you want to see asyncio dubuging info."
    )
    urllib_debug_logging: bool = Field(
        False, description="True if you want to see urllib dubuging info."
    )

    bedrock: BedrockConfig = Field(default_factory=BedrockConfig)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def get_aws_credentials(self) -> Dict[str, Any]:
        creds = {"region_name": self.aws_region}
        if self.aws_access_key_id:
            creds["aws_access_key_id"] = self.aws_access_key_id
        if self.aws_secret_access_key:
            creds["aws_secret_access_key"] = self.aws_secret_access_key
        return creds


settings = Settings()
