import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, Dict

import pandas as pd
from tqdm.asyncio import tqdm

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent))

from config import settings
from src.aws_client import bedrock_manager
from src.data_loader import DataLoader, PromptSample
from src.reporting import ReportGenerator
from src.strategies.strategy_a import StrategyABaseline
from src.strategies.strategy_b import StrategyBStreamMonitor
from src.strategies.strategy_c import StrategyCFastCorrection
from src.utils import get_report_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="LangGraph Streaming Length Control Benchmark"
    )
    parser.add_argument(
        "--strategy",
        type=str,
        choices=["a", "b", "c", "all"],
        default="all",
        help="Benchmark strategy (a=Prompt, b=Monitor, c=Loop, all=Compare)",
    )
    parser.add_argument(
        "--data",
        type=str,
        default="data/mtbench_prompts.parquet",
        help="Path to prompts parquet",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="measurements",
        help="Output directory",
    )
    parser.add_argument(
        "--concurrency", type=int, default=5, help="Number of concurrent requests"
    )
    parser.add_argument(
        "--limit", type=int, default=10, help="Limit number of prompts (0 for all)"
    )
    return parser.parse_args()


def setup_logging() -> None:
    logging.basicConfig(level=logging.INFO, format=settings.logging_format, force=True)

    # Silence noisy libs
    if not settings.boto3_debug_logging:
        logging.getLogger("botocore").setLevel(logging.WARNING)
        logging.getLogger("boto3").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)


async def run_strategy(
    strategy_key: str, strategy_impl: object, args: argparse.Namespace
) -> pd.DataFrame:
    logger = logging.getLogger(__name__)

    # 1. Init AWS Client (Singleton)
    creds = settings.get_aws_credentials()
    bedrock_manager.initialize(
        region_name=creds.get("region_name"),
        aws_access_key_id=creds.get("aws_access_key_id"),
        aws_secret_access_key=creds.get("aws_secret_access_key"),
        max_pool_connections=max(args.concurrency * 2, 50),
        benchmark_workers=args.concurrency,
    )

    # 2. Load Data
    loader = DataLoader(args.data)
    data = loader.load_prompts()
    all_prompts = []
    for samples in data.values():
        all_prompts.extend(samples)

    if args.limit > 0:
        all_prompts = all_prompts[: args.limit]

    logger.info(f"--- Starting Strategy {strategy_key.upper()} ---")
    logger.info(f"Prompts: {len(all_prompts)}, Concurrency: {args.concurrency}")

    # 3. Execution Loop
    sem = asyncio.Semaphore(args.concurrency)

    async def process_sample(sample: PromptSample) -> Dict[str, Any]:
        async with sem:
            try:
                result = await strategy_impl.generate(sample.prompt)
                # Merge sample info with result
                return {
                    "prompt_id": sample.prompt_id,
                    "category": sample.category,
                    "complexity": sample.complexity,
                    "prompt": sample.prompt,
                    **result,
                }
            except Exception as e:
                logger.error(f"Sample {sample.prompt_id} failed: {e}")
                return {
                    "prompt_id": sample.prompt_id,
                    "error": str(e),
                    "strategy": f"strategy_{strategy_key}",
                }

    try:
        tasks = [process_sample(p) for p in all_prompts]
        results = await tqdm.gather(*tasks)

        # 4. Reporting
        df = pd.DataFrame(results)

        # Expand percentiles if present
        if not df.empty and "latency_percentiles" in df.columns:
            # Normalize breakdown metrics if needed (omitted for brevity)
            pass

        report_path = get_report_path(args.output, f"strategy_{strategy_key}")
        df.to_csv(report_path, index=False)

        ReportGenerator.log_summary(df)
        ReportGenerator.save_jsonl(results, report_path)
        ReportGenerator.generate_markdown_report(df, report_path)

        logger.info(f"Strategy {strategy_key.upper()} finished. Report: {report_path}")
        return df

    finally:
        await bedrock_manager.close()


async def run_all_strategies(
    args: argparse.Namespace, strategy_map: Dict[str, Any]
) -> None:
    results_map = {}

    # 1. Run each strategy
    for key, impl in strategy_map.items():
        logging.info(f"\n>>> Running Strategy {key.upper()} in comparison mode <<<")

        # Let's modify run_strategy to return the DataFrame
        df = await run_strategy(key, impl, args)
        results_map[key] = df

    # 2. Generate Comparison
    logging.info("\n>>> Generating Comparison Report <<<")
    ReportGenerator.generate_comparison_report(
        results_map, get_report_path(args.output, "comparison", "csv")
    )


def main() -> None:
    setup_logging()
    args = parse_args()

    strategy_map = {
        "a": StrategyABaseline(),
        "b": StrategyBStreamMonitor(),
        "c": StrategyCFastCorrection(),
    }

    if args.strategy == "all":
        asyncio.run(run_all_strategies(args, strategy_map))
    elif args.strategy in strategy_map:
        asyncio.run(run_strategy(args.strategy, strategy_map[args.strategy], args))
    else:
        logging.error(f"Unknown strategy: {args.strategy}")
        sys.exit(1)


if __name__ == "__main__":
    main()
