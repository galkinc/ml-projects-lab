import logging
import time
from typing import Any, Dict

from langchain_core.messages import HumanMessage

from src.agent import graph
from src.utils import parse_chunk_content

logger = logging.getLogger(__name__)


class GraphAdapter:
    def __init__(self) -> None:
        self.graph = graph

    async def process_stream(self, message: str, thread_id: str) -> Dict[str, Any]:
        """
        Send message to agent and capture streaming metrics.
        """
        config = {"configurable": {"thread_id": thread_id}}
        inputs = {"messages": [HumanMessage(content=message)]}

        start_time = time.perf_counter()
        first_token_time = None

        full_response = ""
        token_times = []
        usage_metadata = {}

        try:
            # We assume the graph uses a ChatModel that supports token-level streaming
            # LangGraph's astream_events v2 is preferred
            async for event in self.graph.astream_events(
                inputs, config=config, version="v2"
            ):
                kind = event["event"]

                # Check for LLM stream events
                if kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]

                    if hasattr(chunk, "usage_metadata") and chunk.usage_metadata:
                        usage_metadata = chunk.usage_metadata

                    text_chunk = parse_chunk_content(
                        chunk.content if hasattr(chunk, "content") else ""
                    )

                    # Only count time if we actually got text
                    if text_chunk:
                        now = time.perf_counter()
                        if first_token_time is None:
                            first_token_time = now

                        token_times.append(now)
                        full_response += text_chunk

                elif kind == "on_chat_model_end":
                    output = event["data"].get("output")
                    if (
                        output
                        and hasattr(output, "usage_metadata")
                        and output.usage_metadata
                    ):
                        usage_metadata = output.usage_metadata

        except Exception as e:
            logger.error(f"Error in streaming: {e}")
            raise

        end_time = time.perf_counter()

        # Calculate Metrics
        ttft_ms = (first_token_time - start_time) * 1000 if first_token_time else None
        e2e_latency_ms = (end_time - start_time) * 1000

        # Metadata tokens
        input_tokens = usage_metadata.get("input_tokens", 0)
        output_tokens = usage_metadata.get("output_tokens", 0)

        # TPS and accurate ITL
        generation_time_sec = (end_time - first_token_time) if first_token_time else 0
        tps = (
            output_tokens / generation_time_sec
            if generation_time_sec > 0 and output_tokens > 0
            else 0
        )

        avg_itl_ms = 0.0
        if output_tokens > 0 and ttft_ms is not None:
            avg_itl_ms = (e2e_latency_ms - ttft_ms) / output_tokens
        elif len(token_times) > 1:
            itl_ms = [
                (token_times[i] - token_times[i - 1]) * 1000
                for i in range(1, len(token_times))
            ]
            avg_itl_ms = sum(itl_ms) / len(itl_ms)

        return {
            "response": full_response,
            "ttft_ms": ttft_ms,
            "e2e_latency_ms": e2e_latency_ms,
            "avg_itl_ms": avg_itl_ms,
            "tps": tps,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "chunk_count": len(token_times),
        }
