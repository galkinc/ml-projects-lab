import logging
import time
from collections.abc import AsyncIterable
from typing import Any

from config import settings
from src.aws_client import bedrock_manager
from src.metrics import calculate_metrics
from src.prompts import BASE_SYSTEM_PROMPT
from src.types import GenerationResult, RawStreamData
from src.utils import get_clean_inference_config

logger = logging.getLogger(__name__)


class StrategyABaseline:
    """
    Strategy A: Optimized Baseline (Prompt + Stop Sequences).

    Mechanism:
    - Uses strict system prompt with few-shot examples.
    - Uses strict inference params (low temp, low maxTokens).
    - Runs on optimized raw aioboto3 client.
    """

    async def _process_stream_events(
        self, stream: AsyncIterable[dict[str, Any]], start_time: float, prompt: str
    ) -> RawStreamData:
        """
        Process all events from converse_stream.
        Collects raw timing and content for centralized metric calculation.
        """
        full_response = ""
        first_token_time = None
        token_times = []
        usage_metadata = {}
        aws_metrics = {}
        stop_reason = None

        try:
            async for event in stream:
                if "contentBlockDelta" in event:
                    text = event["contentBlockDelta"]["delta"]["text"]
                    if text:
                        now = time.perf_counter()
                        if first_token_time is None:
                            first_token_time = now
                        token_times.append(now)
                        full_response += text

                elif "metadata" in event:
                    # Capture usage and server metrics
                    metadata = event.get("metadata", {})
                    usage_metadata = metadata.get("usage", {})
                    aws_metrics = metadata.get("metrics", {})

                elif "messageStop" in event:
                    stop_reason = event["messageStop"].get("stopReason")

        except Exception as e:
            logger.error(f"Stream processing error: {e}", exc_info=True)
            raise

        return {
            "first_token_time": first_token_time,
            "token_times": token_times,
            "usage_metadata": usage_metadata,
            "aws_metrics": aws_metrics,
            "stop_reason": stop_reason,
            "full_response": full_response,
            "start_time": start_time,
            "end_time": 0.0,
            "prompt": prompt,
        }

    async def generate(self, prompt: str) -> GenerationResult:
        """
        Generates response using Bedrock with length constraints.
        """
        start_time = time.perf_counter()

        messages = [{"role": "user", "content": [{"text": prompt}]}]
        system = [{"text": BASE_SYSTEM_PROMPT}]
        max_tokens = settings.bedrock.max_tokens

        try:
            inference_config = get_clean_inference_config(
                temperature=settings.bedrock.temp_strategy_a,
                max_tokens=max_tokens,
                stop_sequences=["\n\n", "Stop."],
            )

            async with bedrock_manager.get_client() as client:
                response = await client.converse_stream(
                    modelId=settings.bedrock.model_id,
                    messages=messages,
                    system=system,
                    inferenceConfig=inference_config,
                )

                # Process stream
                raw_data = await self._process_stream_events(
                    response.get("stream"), start_time, prompt
                )

        except Exception as e:
            logger.error(f"Strategy A generation failed: {e}")
            raise

        end_time = time.perf_counter()
        raw_data["end_time"] = end_time

        # Calculate standardized metrics
        return calculate_metrics(
            data=raw_data, strategy_name="A_prompt_only", max_tokens_limit=max_tokens
        )
