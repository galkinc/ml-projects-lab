import logging

import numpy as np

from config import settings
from src.types import GenerationResult, LatencyPercentiles, RawStreamData

logger = logging.getLogger(__name__)
STALL_THRESHOLD_MS = settings.metrics.stall_threshold_ms
MAX_TOKENS_LIMIT = settings.bedrock.max_tokens


class MetricsCalculator:
    @staticmethod
    def calculate_percentiles(latencies: list[float]) -> LatencyPercentiles:
        """Calculates p50, p90, p95, p99 and other stats."""
        if not latencies:
            return {
                "p50": 0.0,
                "p90": 0.0,
                "p95": 0.0,
                "p99": 0.0,
                "mean": 0.0,
                "min": 0.0,
                "max": 0.0,
                "count": 0,
            }

        # Calculate standard stats
        stats: LatencyPercentiles = {
            "mean": float(np.mean(latencies)),
            "min": float(np.min(latencies)),
            "max": float(np.max(latencies)),
            "count": len(latencies),
            "p50": 0.0,
            "p90": 0.0,
            "p95": 0.0,
            "p99": 0.0,  # defaults
        }

        # Calculate requested percentiles
        for p in settings.metrics.latency_percentile_targets:
            key = f"p{p}"
            if key in stats:  # Only update known keys in TypedDict
                stats[key] = float(np.percentile(latencies, p))  # type: ignore

        return stats


def _normalize_stop_reason(stop_reason: str | None) -> str | None:
    """Normalize AWS stop reason values."""
    if not stop_reason:
        return None
    sr = stop_reason.lower()

    # Normalize to standard values
    if sr in {
        "max_tokens",
        "maxTokens",
        "length",
        "max_length",
        "token_limit_reached",
        "word_limit_reached",
    }:
        return "max_tokens"
    elif sr in {"end_turn", "stop_sequence"}:
        return "end_turn"
    elif sr in {"error", "timeout"}:
        return "error"
    return sr


def calculate_metrics(
    data: RawStreamData,
    strategy_name: str,
    max_tokens_limit: int = MAX_TOKENS_LIMIT,
    stall_threshold_ms: float = STALL_THRESHOLD_MS,
) -> GenerationResult:
    """
    Centralized metric calculation logic.
    Calculates Latency, Throughput (OTPS), Compliance, and Stability metrics.
    """
    start_time = data["start_time"]
    end_time = data["end_time"]
    first_token_time = data["first_token_time"]
    token_times = data.get("token_times", [])
    usage = data["usage_metadata"]
    aws_metrics = data.get("aws_metrics", {})
    response = data["full_response"]
    raw_stop_reason = data["stop_reason"]
    stop_reason = _normalize_stop_reason(raw_stop_reason)
    has_token_mismatch = False  # Validate token consistency

    # 1. Latency Calculations
    ttft_ms = (first_token_time - start_time) * 1000 if first_token_time else None
    e2e_latency_ms = (end_time - start_time) * 1000

    server_latency_ms = aws_metrics.get("latencyMs")
    client_overhead_ms = None

    if server_latency_ms is not None:
        server_latency_ms = float(server_latency_ms)
        client_overhead_ms = max(e2e_latency_ms - server_latency_ms, 0)

    # 2. Token Usage
    output_tokens = usage.get("outputTokens", 0)
    input_tokens = usage.get("inputTokens", 0)

    if output_tokens == 0 and len(token_times) > 0:
        logger.warning(
            f"Token consistency error: {len(token_times)} chunks but 0 output tokens"
            f"Prompt ID: {data.get('prompt_id', 'unknown')}. "
            f"This may indicate AWS API inconsistency."
        )
        has_token_mismatch = True
    elif len(token_times) > 0 and abs(len(token_times) - output_tokens) > 2:
        logger.debug(
            f"Token consistency: {len(token_times)} "
            f"chunks vs {output_tokens} output tokens"
            f"Deviation: {abs(len(token_times) - output_tokens)}. "
            f"Falling back to AWS reported token count."
        )
        has_token_mismatch = True

    # Check if we truly hit the limit
    hit_token_limit = (output_tokens >= max_tokens_limit) and (
        stop_reason == "max_tokens"
    )

    # 3. OTPS Calculation
    otps = 0.0
    if first_token_time and output_tokens > 1:
        decoding_time = end_time - first_token_time
        if decoding_time > 0:
            otps = (output_tokens - 1) / decoding_time
        else:
            otps = 0.0

    # 4. Stability Analysis (Inter-token latencies)
    # Ensure we have valid tokens to count
    if len(token_times) > 1 and output_tokens > 1:
        latencies = [
            (token_times[i] - token_times[i - 1]) * 1000
            for i in range(1, len(token_times))
        ]
        max_inter_token_latency_ms = max(latencies)
        stall_count = sum(1 for lat in latencies if lat > stall_threshold_ms)
        latency_stats = MetricsCalculator.calculate_percentiles(latencies)
    else:
        max_inter_token_latency_ms = 0.0
        stall_count = 0
        latency_stats = {
            "p50": 0.0,
            "p90": 0.0,
            "p95": 0.0,
            "p99": 0.0,
            "mean": 0.0,
            "min": 0.0,
            "max": 0.0,
            "count": 0,
        }

    # 5. Compliance & Validity
    prompt_word_count = len(data["prompt"].split())
    response_word_count = len(response.split())
    is_compliant = (
        settings.bedrock.min_words <= response_word_count <= settings.bedrock.max_words
    )
    word_count_delta = (
        response_word_count
        - (settings.bedrock.min_words + settings.bedrock.max_words) // 2
    )  # Deviation from target center

    has_valid_metrics = bool(
        ttft_ms is not None
        and output_tokens > 0
        and first_token_time is not None
        and len(response.strip()) > 0
    )

    # Logging key anomalies
    if not has_valid_metrics:
        logger.warning(
            f"Invalid metrics for {strategy_name}: "
            f"ttft={ttft_ms}ms, tokens={output_tokens}, response_len={len(response)}"
        )

    if stall_count > 0:
        logger.debug(
            f"Stalls detected: {stall_count}x (max: {max_inter_token_latency_ms:.1f}ms)"
        )

    if hit_token_limit:
        logger.debug(f"Hit token limit: {output_tokens}/{max_tokens_limit}")

    # Default False unless provided
    is_estimated_usage = data.get("is_estimated_usage", False)

    return {
        "response": response,
        "prompt_word_count": prompt_word_count,
        "response_word_count": response_word_count,
        "is_compliant": is_compliant,
        "is_estimated_usage": is_estimated_usage,
        "ttft_ms": ttft_ms,
        "e2e_latency_ms": e2e_latency_ms,
        "server_latency_ms": server_latency_ms,
        "client_overhead_ms": client_overhead_ms,
        "otps": otps,
        "has_valid_metrics": has_valid_metrics,
        "max_inter_token_latency_ms": max_inter_token_latency_ms,
        "stall_count": stall_count,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "hit_token_limit": hit_token_limit,
        "stop_reason": stop_reason,
        "strategy": strategy_name,
        "latency_percentiles": latency_stats,
        "word_count_delta": word_count_delta,
        "first_attempt_compliant": data.get(
            "first_attempt_compliant"
        ),  # None for single-turn
        # Cache placeholders
        "cache_creation_input_tokens": usage.get("cacheCreationInputTokens", 0),
        "cache_read_input_tokens": usage.get("cacheReadInputTokens", 0),
        # Cost metrics (default to single-turn usage if not provided)
        "total_cost_input_tokens": data.get("total_cost_input_tokens", input_tokens),
        "total_cost_output_tokens": data.get("total_cost_output_tokens", output_tokens),
        "num_attempts": data.get("num_attempts", 1),
        "has_token_mismatch": has_token_mismatch,
    }
