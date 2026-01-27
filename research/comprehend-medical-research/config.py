from typing import Any, Dict, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    aws_access_key_id: Optional[str] = Field(None, alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(None, alias="AWS_SECRET_ACCESS_KEY")
    aws_region: str = Field("us-east-1", alias="AWS_REGION")

    examples_path: str = Field("examples", description="Path to the text samples with")
    aws_comp_output_path: str = Field("results/aws_comprehend", description="Path to uut results for AWS Comprehend Medical")
    aws_comp_limit: int = Field(10000, description="AWS Comprehend Medical max chars per request")

    logging_level: str = Field(default="DEBUG", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    logging_format: str = Field(
        default="%(asctime)s UTC - %(levelname)s - %(message)s",
        description="Log message format with UTC timezone",
    )
    boto3_logging: bool = Field(True, description="True if you want to see boto3 dubuging info.")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def get_boto_kwargs(self) -> Dict[str, Any]:
        if self.aws_access_key_id and self.aws_secret_access_key:
            return {
                "aws_access_key_id": self.aws_access_key_id,
                "aws_secret_access_key": self.aws_secret_access_key,
                "region_name": self.aws_region,
            }
        return {"region_name": self.aws_region}

settings = Settings()
