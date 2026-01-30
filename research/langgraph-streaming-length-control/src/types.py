from typing import Any, NotRequired, Protocol, TypedDict


class LatencyPercentiles(TypedDict):
    p50: float
    p90: float
    p95: float
    p99: float
    mean: float
    min: float
    max: float
    count: int


class RawStreamData(TypedDict):
    """Raw data collected during streaming."""

    start_time: float
    end_time: float
    first_token_time: float | None
    token_times: list[float]
    usage_metadata: dict[str, Any]
    aws_metrics: dict[str, Any]
    stop_reason: str | None
    full_response: str
    prompt: str
    # Optional fields for multi-turn strategies
    total_cost_input_tokens: NotRequired[int]
    total_cost_output_tokens: NotRequired[int]
    num_attempts: NotRequired[int]
    is_estimated_usage: NotRequired[bool]
    first_attempt_compliant: NotRequired[bool]


class GenerationResult(TypedDict):
    """Final calculated metrics for reports."""

    response: str
    prompt_word_count: int
    response_word_count: int
    is_compliant: bool
    is_estimated_usage: bool

    # Latency Metrics
    ttft_ms: float | None
    e2e_latency_ms: float
    server_latency_ms: float | None
    client_overhead_ms: float | None
    otps: float

    # Stability Metrics
    has_valid_metrics: bool
    max_inter_token_latency_ms: float
    stall_count: int

    # Token Usage
    input_tokens: int
    output_tokens: int
    hit_token_limit: bool
    stop_reason: str | None

    strategy: str
    latency_percentiles: LatencyPercentiles

    # Cache metrics
    cache_creation_input_tokens: int
    cache_read_input_tokens: int

    # Cost metrics (for multi-turn strategies)
    total_cost_input_tokens: int
    total_cost_output_tokens: int
    num_attempts: int

    # Extended metrics
    word_count_delta: int
    first_attempt_compliant: bool | None
    has_token_mismatch: bool


# Protocol for Strategy Pattern
class LengthControlStrategy(Protocol):
    async def generate(self, prompt: str) -> GenerationResult:
        """Generate a response based on the prompt."""
        ...
