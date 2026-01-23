import asyncio
import logging
import time
from typing import Any, Dict

import pandas as pd
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage
from tqdm.asyncio import tqdm

from config import settings
from src.data_loader import DataLoader, PromptSample
from src.reporting import ReportGenerator
from src.utils import get_report_path, parse_chunk_content

logger = logging.getLogger(__name__)


class LangChainAWSBenchmark:
    """
    Benchmarks ChatBedrock from langchain-aws library directly,
    without LangGraph state management.
    """

    def __init__(self) -> None:
        creds = settings.get_aws_credentials()
        self.model = ChatBedrock(
            model_id=settings.bedrock.model_id,
            region_name=creds.get("region_name"),
            aws_access_key_id=creds.get("aws_access_key_id"),
            aws_secret_access_key=creds.get("aws_secret_access_key"),
            model_kwargs={"temperature": settings.bedrock.temperature},
            streaming=True,
        )

    async def call_model_stream(self, message: str) -> dict:
        start_time = time.perf_counter()
        first_token_time = None
        token_times = []
        usage_metadata = {}
        full_response = ""

        try:
            # Direct streaming call via LangChain (ChatBedrock)
            async for chunk in self.model.astream([HumanMessage(content=message)]):
                if hasattr(chunk, "usage_metadata") and chunk.usage_metadata:
                    usage_metadata = chunk.usage_metadata

                text_chunk = parse_chunk_content(chunk.content)
                if text_chunk:
                    now = time.perf_counter()
                    if first_token_time is None:
                        first_token_time = now
                    token_times.append(now)
                    full_response += text_chunk
        except Exception as e:
            logger.error(f"LangChain AWS call failed: {e}")
            raise

        end_time = time.perf_counter()

        # Metrics calculation
        ttft_ms = (first_token_time - start_time) * 1000 if first_token_time else None
        e2e_latency_ms = (end_time - start_time) * 1000

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


async def run_langchain_aws_benchmark(
    prompts_path: str, output_path: str, concurrency: int, limit: int
) -> pd.DataFrame:

    # Load Data
    loader = DataLoader(prompts_path)
    data = loader.load_prompts()
    all_prompts = []
    for samples in data.values():
        all_prompts.extend(samples)

    if limit > 0:
        all_prompts = all_prompts[:limit]

    logger.info(
        "Starting LANGCHAIN-AWS benchmark. "
        "Samples: {len(all_prompts)}, Concurrency: {concurrency}"
    )

    # Init Service
    benchmark = LangChainAWSBenchmark()
    sem = asyncio.Semaphore(concurrency)

    async def process_sample(sample: PromptSample) -> Dict[str, Any]:

        async with sem:
            try:
                res = await benchmark.call_model_stream(sample.prompt)
                res.update(
                    {
                        "prompt_id": sample.prompt_id,
                        "category": sample.category,
                        "complexity": sample.complexity,
                        "prompt": sample.prompt,
                        "tps": res["tps"],
                        "input_tokens": res["input_tokens"],
                        "output_tokens": res["output_tokens"],
                        "chunk_count": res["chunk_count"],
                        "error": None,
                    }
                )
                return res

            except Exception as e:
                return {"prompt_id": sample.prompt_id, "error": str(e)}

    # Execution
    tasks = [process_sample(p) for p in all_prompts]
    results = await tqdm.gather(*tasks)

    # Reporting
    df = pd.DataFrame(results)

    final_path = get_report_path("measurements", "langchain_aws")
    df.to_csv(final_path, index=False)

    # Log and Generate reports
    ReportGenerator.log_summary(df)
    ReportGenerator.save_jsonl(results, final_path)
    ReportGenerator.generate_markdown_report(df, final_path)

    logger.info(f"LANGCHAIN-AWS finished. Results: {final_path}")
    return df


if __name__ == "__main__":
    import argparse

    from main import setup_logging

    setup_logging()

    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--concurrency", type=int, default=2)
    args = parser.parse_args()

    asyncio.run(
        run_langchain_aws_benchmark(
            prompts_path="data/mtbench_prompts.parquet",
            output_path="measurements/langchain_aws/lc_aws.csv",
            concurrency=args.concurrency,
            limit=args.limit,
        )
    )
