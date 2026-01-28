import datetime
import logging
import os
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def parse_chunk_content(chunk_content: str | list[dict[str, str]]) -> str:
    """Helper to extract text from various chunk formats."""
    if isinstance(chunk_content, str):
        return chunk_content
    elif isinstance(chunk_content, list):
        # Handle list of content blocks if necessary
        text = ""
        for block in chunk_content:
            if isinstance(block, dict) and "text" in block:
                text += block["text"]
        return text
    return ""


def get_report_path(base_dir: str, prefix: str, extension: str = "csv") -> str:
    """Generates a timestamped file path."""
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"{prefix}_{timestamp}.{extension}"

    # Ensure directory exists
    os.makedirs(base_dir, exist_ok=True)

    # Create subfolder for strategy to keep it clean
    if "strategy_" in prefix:
        strategy_dir = os.path.join(base_dir, prefix)
        os.makedirs(strategy_dir, exist_ok=True)
        return os.path.join(strategy_dir, filename)

    return os.path.join(base_dir, filename)


def get_clean_inference_config(
    temperature: float, max_tokens: int, stop_sequences: List[str] | None = None
) -> Dict[str, Any]:
    """
    Constructs a valid inferenceConfig for Bedrock Converse API.
    Filters out invalid/blank stop sequences to prevent ValidationException.
    """
    config = {
        "temperature": temperature,
        "maxTokens": max_tokens,
    }

    if stop_sequences:
        # Filter out empty or whitespace-only strings which Bedrock rejects
        valid_stops = [s for s in stop_sequences if s and s.strip()]
        if valid_stops:
            config["stopSequences"] = valid_stops

    return config
