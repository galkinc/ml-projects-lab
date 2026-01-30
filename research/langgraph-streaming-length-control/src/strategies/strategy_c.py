import logging
import time
from typing import Any

from config import settings
from src.aws_client import bedrock_manager
from src.metrics import calculate_metrics
from src.prompts import BASE_SYSTEM_PROMPT, RETRY_PROMPT_TEMPLATE
from src.types import GenerationResult
from src.utils import get_clean_inference_config

logger = logging.getLogger(__name__)


class StrategyCFastCorrection:
    """
    Strategy C: Generate -> Evaluate -> Retry loop.
    Multi-attempt agentic repair for guaranteed compliance.
    """

    async def _generate_once(
        self,
        client: Any,  # noqa
        messages: list[dict],
        attempt: int = 1,
        max_tokens: int = settings.bedrock.max_tokens,
    ) -> tuple[str, dict]:
        """
        Single generation attempt.
        """
        start_attempt = time.perf_counter()
        system = [{"text": BASE_SYSTEM_PROMPT}]

        full_response = ""
        first_token_time = None
        token_times = []
        usage_metadata = {}
        aws_metrics = {}
        stop_reason = None

        try:
            # Dynamic temperature: increase on retry to escape local minima
            temp = settings.bedrock.temp_strategy_c_base
            if attempt > 1:
                temp = settings.bedrock.temp_strategy_c_retry

            inference_config = get_clean_inference_config(
                temperature=temp,
                max_tokens=max_tokens,
                stop_sequences=["\n\n", "Stop."],
            )

            response = await client.converse_stream(
                modelId=settings.bedrock.model_id,
                messages=messages,
                system=system,
                inferenceConfig=inference_config,
            )

            async for event in response.get("stream", []):
                if "contentBlockDelta" in event:
                    text = event["contentBlockDelta"]["delta"]["text"]
                    if text:
                        now = time.perf_counter()
                        if first_token_time is None:
                            first_token_time = now
                        token_times.append(now)
                        full_response += text

                elif "metadata" in event:
                    metadata = event.get("metadata", {})
                    usage_metadata = metadata.get("usage", {})
                    aws_metrics = metadata.get("metrics", {})

                elif "messageStop" in event:
                    stop_reason = event["messageStop"].get("stopReason")

        except Exception as e:
            logger.error(f"Generation attempt {attempt} failed: {e}")
            raise

        end_attempt = time.perf_counter()

        return full_response, {
            "first_token_time": first_token_time,
            "token_times": token_times,
            "usage_metadata": usage_metadata,
            "aws_metrics": aws_metrics,
            "stop_reason": stop_reason,
            "attempt_time": end_attempt - start_attempt,
            "attempt_number": attempt,
        }

    def _evaluate_compliance(self, response: str) -> bool:
        """Check if response is 8-12 words."""
        word_count = len(response.split())
        return 8 <= word_count <= 12

    async def generate(self, prompt: str) -> GenerationResult:
        """Generate with retry loop until compliant."""
        start_time = time.perf_counter()
        max_tokens = settings.bedrock.max_tokens
        compliance_regeneration_attempts = (
            settings.bedrock.compliance_regeneration_attempts
        )

        attempt = 1
        all_attempts = []

        current_messages = [{"role": "user", "content": [{"text": prompt}]}]

        try:
            async with bedrock_manager.get_client() as client:
                while attempt <= compliance_regeneration_attempts:
                    response_text, attempt_meta = await self._generate_once(
                        client, current_messages, attempt=attempt, max_tokens=max_tokens
                    )

                    all_attempts.append((response_text, attempt_meta))
                    is_compliant = self._evaluate_compliance(response_text)

                    logger.debug(
                        f"Attempt {attempt}: '{response_text}' "
                        f"({len(response_text.split())} words) - "
                        f"Compliant: {is_compliant}"
                    )

                    if is_compliant or attempt >= compliance_regeneration_attempts:
                        break

                    # Prepare retry
                    word_count = len(response_text.split())
                    retry_prompt = RETRY_PROMPT_TEMPLATE.format(
                        word_count=word_count, original_prompt=prompt
                    )

                    # Add history to context
                    current_messages.append(
                        {"role": "assistant", "content": [{"text": response_text}]}
                    )
                    current_messages.append(
                        {"role": "user", "content": [{"text": retry_prompt}]}
                    )

                    attempt += 1

        except Exception as e:
            logger.error(f"Strategy C generation failed: {e}")
            raise

        # Use the final attempt for metrics
        final_response, final_meta = all_attempts[-1]
        end_time = time.perf_counter()

        # Build aggregated raw_data

        # Calculate total token usage across all attempts
        total_input = sum(
            a[1].get("usage_metadata", {}).get("inputTokens", 0) for a in all_attempts
        )
        total_output = sum(
            a[1].get("usage_metadata", {}).get("outputTokens", 0) for a in all_attempts
        )

        # CORRECT: usage_metadata contains only FINAL attempt stats for OTPS calculation
        final_usage = final_meta.get("usage_metadata", {})

        raw_data = {
            "first_token_time": final_meta.get("first_token_time"),
            "token_times": final_meta.get("token_times", []),
            "usage_metadata": final_usage,  # <-- FIX: Use final attempt usage
            "aws_metrics": final_meta.get("aws_metrics", {}),
            "stop_reason": final_meta.get("stop_reason"),
            "full_response": final_response,
            "start_time": start_time,
            "end_time": end_time,
            "prompt": prompt,
            # Pass aggregated costs to metrics
            "total_cost_input_tokens": total_input,
            "total_cost_output_tokens": total_output,
            "num_attempts": len(all_attempts),
            "first_attempt_compliant": len(all_attempts) == 1,
        }

        result = calculate_metrics(
            data=raw_data,
            strategy_name="C_fast_correction",
            max_tokens_limit=max_tokens,
        )

        return result
