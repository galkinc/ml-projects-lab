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


class StrategyBStreamMonitor:
    """
    Strategy B: Active token counting during streaming.
    Closes stream when token limit reached.
    """

    async def _process_stream_with_cutoff(
        self,
        stream: AsyncIterable[dict[str, Any]],
        start_time: float,
        prompt: str,
        max_words: int = settings.bedrock.max_words,
    ) -> RawStreamData:
        """
        Process stream with ACTIVE TOKEN COUNTING.
        Stops yielding when token_count > max_tokens.
        """
        full_response = ""
        first_token_time = None
        token_times = []
        usage_metadata = {}
        aws_metrics = {}
        stop_reason = None
        chunk_count = 0

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
                        chunk_count += 1

                        current_word_count = len(full_response.split())
                        if current_word_count >= max_words:
                            logger.debug(
                                f"Word limit reached: "
                                f"{current_word_count} >= {max_words}"
                            )
                            stop_reason = "word_limit_reached"
                            break

                elif "metadata" in event:
                    metadata = event.get("metadata", {})
                    usage_metadata = metadata.get("usage", {})
                    aws_metrics = metadata.get("metrics", {})

                elif "messageStop" in event:
                    stop_reason = event["messageStop"].get("stopReason")
                    # CRITICAL FIX: Estimate usage if cutoff happened before metadata
            if stop_reason == "word_limit_reached" and not usage_metadata:
                est_output = max(chunk_count, int(len(full_response.split()) * 1.3))
                usage_metadata = {
                    "inputTokens": 0,  # Unknown without tokenizer
                    "outputTokens": est_output,
                }
                logger.info(
                    f"Stream cutoff at word_limit. Estimated tokens={est_output} "
                    f"from {chunk_count} chunks."
                )
                is_estimated = True
            else:
                is_estimated = False

        except Exception as e:
            logger.error(f"Stream processing error: {e}", exc_info=True)
            raise

        return {
            "first_token_time": first_token_time,
            "token_times": token_times,
            "usage_metadata": usage_metadata,
            "aws_metrics": aws_metrics,
            "is_estimated_usage": is_estimated,
            "stop_reason": stop_reason,
            "full_response": full_response,
            "start_time": start_time,
            "end_time": 0.0,
            "prompt": prompt,
        }

    async def generate(self, prompt: str) -> GenerationResult:
        """Generates with active token counting."""
        start_time = time.perf_counter()

        messages = [{"role": "user", "content": [{"text": prompt}]}]
        system = [{"text": BASE_SYSTEM_PROMPT}]
        max_tokens = settings.bedrock.max_tokens

        try:
            async with bedrock_manager.get_client() as client:
                inference_config = get_clean_inference_config(
                    temperature=settings.bedrock.temp_strategy_b,
                    max_tokens=max_tokens,
                    stop_sequences=["\n\n", "Stop."],
                )

                response = await client.converse_stream(
                    modelId=settings.bedrock.model_id,
                    messages=messages,
                    system=system,
                    inferenceConfig=inference_config,
                )

                raw_data = await self._process_stream_with_cutoff(
                    response.get("stream"),
                    start_time,
                    prompt,
                    max_words=settings.bedrock.max_words,
                )

        except Exception as e:
            logger.error(f"Strategy B generation failed: {e}")
            raise

        end_time = time.perf_counter()
        raw_data["end_time"] = end_time

        return calculate_metrics(
            data=raw_data, strategy_name="B_stream_monitor", max_tokens_limit=max_tokens
        )
