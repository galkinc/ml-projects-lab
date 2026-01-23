import asyncio
import logging
import argparse
import uuid
import pandas as pd
from tqdm.asyncio import tqdm

from config import settings
from src.data_loader import DataLoader
from src.graph_adapter import GraphAdapter
from src.reporting import ReportGenerator
from src.utils import get_report_path

logger = logging.getLogger(__name__)

class BenchmarkRunner:
    def __init__(self, base_dir: str = "measurements"):
        self.base_dir = base_dir

    async def run(
        self,
        prompts_path: str,
        concurrency: int,
        limit: int
    ):
        # 1. Load Data
        logger.info("Loading prompts...")
        loader = DataLoader(prompts_path)
        try:
            data = loader.load_prompts()
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            return

        all_prompts = []
        for complexity, samples in data.items():
            all_prompts.extend(samples)
        
        if limit > 0:
            all_prompts = all_prompts[:limit]
            logger.info(f"Limiting benchmark to first {limit} prompts.")

        logger.info(f"Total prompts to process: {len(all_prompts)}")

        # 2. Init Adapter
        adapter = GraphAdapter()

        # 3. Run Benchmark Loop
        logger.info(f"Starting benchmark with concurrency={concurrency}...")
        sem = asyncio.Semaphore(concurrency)

        async def process_sample(sample):
            # Generate unique thread_id to keep conversations separate in MemorySaver
            thread_id = str(uuid.uuid4())
            
            async with sem:
                try:
                    res = await adapter.process_stream(sample.prompt, thread_id)
                    return {
                        "prompt_id": sample.prompt_id,
                        "category": sample.category,
                        "complexity": sample.complexity,
                        "prompt": sample.prompt,
                        "prompt_length": len(sample.prompt),
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
                    logger.error(f"Error processing prompt {sample.prompt_id}: {e}")
                    return {
                        "prompt_id": sample.prompt_id,
                        "category": sample.category,
                        "complexity": sample.complexity,
                        "prompt": sample.prompt,
                        "prompt_length": len(sample.prompt),
                        "response": "",
                        "ttft_ms": None,
                        "e2e_latency_ms": None,
                        "avg_itl_ms": None,
                        "token_count": 0,
                        "error": str(e)
                    }

        tasks = [process_sample(p) for p in all_prompts]
        results = await tqdm.gather(*tasks)

        # 4. Save and Report
        df = pd.DataFrame(results)
        final_output_path = get_report_path(self.base_dir, "langgraph")

        df.to_csv(final_output_path, index=False)
        logger.info(f"Results saved to {final_output_path}")

        # Metrics Summary
        logger.info("=== Benchmark Summary ===")
        if "ttft_ms" in df.columns:
             logger.info(f"Avg TTFT: {df['ttft_ms'].mean():.2f} ms")
        if "e2e_latency_ms" in df.columns:
             logger.info(f"Avg E2E: {df['e2e_latency_ms'].mean():.2f} ms")
        
        # Detailed metrics if needed
        ReportGenerator.log_summary(df)

        # 5. Generate Reports
        results_list = df.to_dict(orient="records")
        ReportGenerator.save_jsonl(results_list, final_output_path)
        ReportGenerator.generate_markdown_report(df, final_output_path)
        return df

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LangGraph Latency Benchmark")
    parser.add_argument("--data", type=str, default="data/mtbench_prompts.parquet", help="Path to prompts parquet")
    parser.add_argument("--output", type=str, default="measurements/benchmark.csv", help="Output CSV path pattern")
    parser.add_argument("--concurrency", type=int, default=5, help="Number of concurrent requests")
    parser.add_argument("--limit", type=int, default=10, help="Limit number of prompts (0 for all)")

    args = parser.parse_args()

    runner = BenchmarkRunner(args.output)
    asyncio.run(runner.run(
        prompts_path=args.data,
        concurrency=args.concurrency,
        limit=args.limit
    ))
