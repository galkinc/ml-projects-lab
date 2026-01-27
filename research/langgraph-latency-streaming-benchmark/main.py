import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent))

from config import settings
from src.baseline_raw import run_baseline_benchmark
from src.benchmark import BenchmarkRunner
from src.langchain_aws_benchmark import run_langchain_aws_benchmark
from src.utils import get_report_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LangGraph Latency Benchmark")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["langgraph", "baseline", "langchain_aws", "all"],
        default="langgraph",
        help="Benchmark mode",
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
        default="measurements/benchmark.csv",
        help="Output CSV path pattern",
    )
    parser.add_argument(
        "--concurrency", type=int, default=5, help="Number of concurrent requests"
    )
    parser.add_argument(
        "--limit", type=int, default=10, help="Limit number of prompts (0 for all)"
    )
    return parser.parse_args()


def setup_logging() -> None:
    # 1. Set global logging to INFO by default
    base_level = logging.INFO

    logging.basicConfig(level=base_level, format=settings.logging_format, force=True)

    # 2. Control noisy libraries based on config
    if not settings.asyncio_debug_logging:
        logging.getLogger("asyncio").setLevel(logging.WARNING)

    if not settings.boto3_debug_logging:
        logging.getLogger("botocore").setLevel(logging.WARNING)
        logging.getLogger("boto3").setLevel(logging.WARNING)

    if not settings.urllib_debug_logging:
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)

    # 3. Enable DEBUG for our app code if requested
    if settings.logging_level == "DEBUG":
        logging.getLogger("src").setLevel(logging.DEBUG)
        logging.getLogger("__main__").setLevel(logging.DEBUG)
    else:
        logging.getLogger("src").setLevel(logging.INFO)


def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)

    args = parse_args()

    logger.info("Starting Benchmark CLI")
    logger.info(
        f"Mode: {args.mode}, Concurrency={args.concurrency}, Limit={args.limit}"
    )

    df_map = {}

    try:
        if args.mode in ["langgraph", "all"]:
            logger.info("--- Running LangGraph Mode ---")
            runner = BenchmarkRunner("measurements")
            df_map["langgraph"] = asyncio.run(
                runner.run(
                    prompts_path=args.data,
                    concurrency=args.concurrency,
                    limit=args.limit,
                )
            )

        if args.mode in ["baseline", "all"]:
            logger.info("--- Running RAW Baseline Mode ---")
            df_map["baseline"] = asyncio.run(
                run_baseline_benchmark(
                    prompts_path=args.data,
                    output_path="measurements",  # Base dir
                    concurrency=args.concurrency,
                    limit=args.limit,
                )
            )

        if args.mode in ["langchain_aws", "all"]:
            logger.info("--- Running LangChain AWS Mode (No Graph) ---")
            df_map["langchain_aws"] = asyncio.run(
                run_langchain_aws_benchmark(
                    prompts_path=args.data,
                    output_path="measurements",  # Base dir
                    concurrency=args.concurrency,
                    limit=args.limit,
                )
            )

        # 4. Global Comparison
        if args.mode == "all" and len(df_map) > 1:
            from src.reporting import ReportGenerator

            logger.info("--- Generating Global Comparison Report ---")

            comparison_path = get_report_path(
                "measurements", "comparison", extension="csv"
            )
            ReportGenerator.generate_comparison_report(df_map, comparison_path)

    except KeyboardInterrupt:
        logger.warning("Benchmark interrupted by user.")
        sys.exit(130)
    except Exception:
        logger.exception("Fatal error during benchmark execution")
        sys.exit(1)


if __name__ == "__main__":
    main()
