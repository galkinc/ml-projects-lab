from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BedrockConfig(BaseSettings):
    model_id: str = Field("us.amazon.nova-micro-v1:0", alias="BEDROCK_MODEL_ID")
    temperature: float = Field(0.1, alias="BEDROCK_TEMPERATURE")
    temp_strategy_a: float = Field(0.1, alias="TEMP_STRATEGY_A")
    temp_strategy_b: float = Field(0.1, alias="TEMP_STRATEGY_B")
    temp_strategy_c_base: float = Field(0.1, alias="TEMP_STRATEGY_C_BASE")
    temp_strategy_c_retry: float = Field(0.2, alias="TEMP_STRATEGY_C_RETRY")
    min_words: int = Field(8, alias="MIN_WORDS")
    max_words: int = Field(12, alias="MAX_WORDS")
    max_tokens: int = Field(30, alias="MAX_TOKENS")
    compliance_regeneration_attempts: int = Field(
        2,
        description="Maximum number of regeneration attempts when generated content "
        "fails compliance checks (e.g., response length requirements). "
        "Each regeneration creates a completely new LLM request.",
    )


class Metrics(BaseSettings):
    stall_threshold_ms: float = Field(
        300.0,
        description="Threshold (ms) to consider inter-token latency as a 'stall'.",
    )
    latency_percentile_targets: list[int] = Field(
        default=[50, 90, 95, 99],
        description="Standard percentiles for latency analysis.",
    )


class Reporting(BaseSettings):
    top_n_samples_to_show: int = Field(
        80, description="Number of detailed samples to include in markdown reports.."
    )


class Infrastructure(BaseSettings):
    """
    -   High concurrency (many concurrent requests):
        max_pool_connections=100 connect_timeout=5.0 read_timeout=120.0
    -   Moderate concurrency (typical for APIs):
        max_pool_connections=50 connect_timeout=10.0 read_timeout=60.0
    -   Low concurrency (batch processing) :
        max_pool_connections=20 connect_timeout=15.0 read_timeout=300.0
    """

    global_timeout: float = Field(120.0, alias="GLOBAL_TIMEOUT")
    # ==================== AWS Client ====================
    max_pool_connections: int = Field(
        30, description="Minimum connection pool size regardless of worker count."
    )
    connect_timeout: float = Field(
        10.0, description="Timeout for establishing TCP connection to Bedrock endpoint."
    )
    read_timeout: float = Field(
        60.0,
        description="Timeout for reading response from Bedrock (single read operation).",
    )
    max_attempts: int = Field(
        5, description="Max retries attepts during the AWS cleint initiation."
    )
    pool_scaling_factor: int = Field(
        2,
        description="Connection pool scaling: pool_size = workers * FACTOR. "
        "Ensures sufficient sockets for concurrent requests without exhaustion. "
        "Typical: factor 2 reserves 2 connections per worker.",
    )
    default_min_pool_connnections: int = Field(
        50, description="Minimum connection pool size regardless of worker count."
    )
    shutdown_grace_period_sec: float = Field(
        0.6,
        description="Grace period (seconds) to allow aiohttp connectors to close gracefully."
        "Too short: connections not fully closed, resource leaks."
        "Too long: slow shutdown. 0.25s is sweet spot.",
    )


class DataLoaderConfig(BaseSettings):
    tokens_per_word_estimate: float = Field(
        1.3,
        description="Approximation factor for token count based on word count. "
        "Based on Claude tokenizer analysis: 1 word ≈ 1.3 tokens on average.",
    )
    complexity_thresholds: dict[str, float] = Field(
        default={"Low": 50.0, "Medium": 100.0, "High": float("inf")},
        description="Token count thresholds for prompt categorization.",
    )
    complexity_categories_map: dict[str, list[str]] = Field(
        default={
            "High": ["math", "coding"],
            "Medium": ["roleplay", "reasoning"],
            "Low": [],
        },
        description="Categories that map directly to complexity levels.",
    )


class Settings(BaseSettings):
    aws_access_key_id: str | None = Field(None, alias="AWS_ACCESS_KEY_ID")

    aws_secret_access_key: str | None = Field(None, alias="AWS_SECRET_ACCESS_KEY")
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
    infra: Infrastructure = Field(default_factory=Infrastructure)
    metrics: Metrics = Field(default_factory=Metrics)
    reporting: Reporting = Field(default_factory=Reporting)
    data_loader: DataLoaderConfig = Field(default_factory=DataLoaderConfig)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def get_aws_credentials(self) -> dict[str, str | None]:
        creds = {"region_name": self.aws_region}
        if self.aws_access_key_id:
            creds["aws_access_key_id"] = self.aws_access_key_id
        if self.aws_secret_access_key:
            creds["aws_secret_access_key"] = self.aws_secret_access_key
        return creds


settings = Settings()
