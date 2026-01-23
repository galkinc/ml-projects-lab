import os
from datetime import datetime, timezone
from typing import Dict, List, Union


def parse_chunk_content(
    content: Union[
        str, List[Union[str, Dict[str, Union[str, int, float, bool, None]]]], None
    ],
) -> str:
    """
    Parses the content of an LLM chunk which might be a string,
    a list of dicts (Bedrock/Nova style), or mixed types.
    """
    if not content:
        return ""

    text_chunk = ""

    if isinstance(content, list):
        # Handle list of dicts (e.g. [{'type': 'text', 'text': '...'}])
        for c in content:
            if isinstance(c, dict) and c.get("type") == "text":
                text_chunk += c.get("text", "")
            elif isinstance(c, str):
                text_chunk += c
            else:
                text_chunk += str(c)
    elif isinstance(content, str):
        text_chunk = content
    else:
        text_chunk = str(content)

    return text_chunk


def get_utc_timestamp() -> str:
    """Returns a filename-friendly UTC timestamp in ISO-like format."""
    # Example: 20240123T153045Z
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def ensure_dir(path: str) -> None:
    """Ensures directory exists."""
    os.makedirs(os.path.dirname(path), exist_ok=True)


def get_report_path(base_dir: str, prefix: str, extension: str = "csv") -> str:
    """
    Generates a standardized timestamped path:
    measurements/prefix/prefix_timestamp.ext
    """
    timestamp = get_utc_timestamp()
    path = os.path.join(base_dir, prefix, f"{prefix}_{timestamp}.{extension}")
    ensure_dir(path)
    return path
