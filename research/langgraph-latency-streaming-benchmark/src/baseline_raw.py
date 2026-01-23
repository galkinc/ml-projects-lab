import asyncio
import logging
import time
import pandas as pd
from tqdm.asyncio import tqdm
import aioboto3

from config import settings
from src.data_loader import DataLoader
from src.reporting import ReportGenerator
from src.utils import get_report_path

logger = logging.getLogger(__name__)

class RawBedrockBaseline:
    """
    A baseline implementation that calls AWS Bedrock directly using aioboto3,
    bypassing LangChain and LangGraph entirely.
    """
    def __init__(self):
        self.session = aioboto3.Session()
        self.creds = settings.get_aws_credentials()

    async def call_bedrock_stream(self, message: str) -> dict:
        """Calls Bedrock converse_stream and measures raw latency."""
        start_time = time.perf_counter()
        first_token_time = None
        token_times = []
        full_response = ""
        usage_metadata = {}

        # Construct messages in AWS Bedrock format
        bedrock_messages = [
            {"role": "user", "content": [{"text": message}]}
        ]

        try:
            async with self.session.client(
                "bedrock-runtime",
                **self.creds
            ) as bedrock_runtime:
                response = await bedrock_runtime.converse_stream(
                    modelId=settings.bedrock.model_id,
                    messages=bedrock_messages,
                    inferenceConfig={
                        "temperature": settings.bedrock.temperature,
                        "maxTokens": 1024, # Standard for baseline
                    },
                )

                stream = response.get("stream")
                if stream:
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
                            usage_metadata = event["metadata"].get("usage", {})
        except Exception as e:
            logger.error(f"Raw Bedrock call failed: {e}")
            raise

        end_time = time.perf_counter()

        # Metrics calculation
        ttft_ms = (first_token_time - start_time) * 1000 if first_token_time else None
        e2e_latency_ms = (end_time - start_time) * 1000
        
        input_tokens = usage_metadata.get("inputTokens", 0)
        output_tokens = usage_metadata.get("outputTokens", 0)

        # TPS and accurate ITL
        generation_time_sec = (end_time - first_token_time) if first_token_time else 0
        tps = output_tokens / generation_time_sec if generation_time_sec > 0 and output_tokens > 0 else 0

        avg_itl_ms = 0.0
        if output_tokens > 0 and ttft_ms is not None:
             avg_itl_ms = (e2e_latency_ms - ttft_ms) / output_tokens
        elif len(token_times) > 1:
            itl_ms = [(token_times[i] - token_times[i-1]) * 1000 for i in range(1, len(token_times))]
            avg_itl_ms = sum(itl_ms) / len(itl_ms)

        return {
            "response": full_response,
            "ttft_ms": ttft_ms,
            "e2e_latency_ms": e2e_latency_ms,
            "avg_itl_ms": avg_itl_ms,
            "tps": tps,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "chunk_count": len(token_times)
        }

async def run_baseline_benchmark(
    prompts_path: str,
    output_path: str,
    concurrency: int,
    limit: int
):
    # 1. Load Data
    loader = DataLoader(prompts_path)
    data = loader.load_prompts()
    all_prompts = []
    for samples in data.values():
        all_prompts.extend(samples)
    
    if limit > 0:
        all_prompts = all_prompts[:limit]

    logger.info(f"Starting RAW BASELINE benchmark. Samples: {len(all_prompts)}, Concurrency: {concurrency}")

    # 2. Init Raw Service
    baseline = RawBedrockBaseline()
    sem = asyncio.Semaphore(concurrency)

    async def process_sample(sample):
        async with sem:
            try:
                res = await baseline.call_bedrock_stream(sample.prompt)
                return {
                    "prompt_id": sample.prompt_id,
                    "category": sample.category,
                    "complexity": sample.complexity,
                    "prompt": sample.prompt,
                    "response": res["response"],
                    "ttft_ms": res["ttft_ms"],
                    "e2e_latency_ms": res["e2e_latency_ms"],
                    "avg_itl_ms": res["avg_itl_ms"],
                    "tps": res["tps"],
                    "input_tokens": res["input_tokens"],
                    "output_tokens": res["output_tokens"],
                    "chunk_count": res["chunk_count"],
                    "error": None
                }
            except Exception as e:
                return {"prompt_id": sample.prompt_id, "error": str(e)}

    # 3. Execution
    tasks = [process_sample(p) for p in all_prompts]
    results = await tqdm.gather(*tasks)

    # Reporting
    df = pd.DataFrame(results)
    
    final_path = get_report_path("measurements", "baseline")
    df.to_csv(final_path, index=False)
    
    # Log and Generate reports
    ReportGenerator.log_summary(df)
    ReportGenerator.save_jsonl(results, final_path)
    ReportGenerator.generate_markdown_report(df, final_path)
    
    logger.info(f"RAW BASELINE finished. Results: {final_path}")
    return df

if __name__ == "__main__":
    # This file can be run directly: uv run python -m src.baseline_raw --limit 5 --concurrency 2
    import argparse
    from main import setup_logging
    setup_logging()
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--concurrency", type=int, default=2)
    args = parser.parse_args()

    asyncio.run(run_baseline_benchmark(
        prompts_path="data/mtbench_prompts.parquet",
        output_path="measurements/baseline/raw.csv",
        concurrency=args.concurrency,
        limit=args.limit
    ))
