import json
import logging
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from config import settings
from src.metrics import MetricsCalculator

logger = logging.getLogger(__name__)


TOP_N_SAMPLES_TO_SHOW = settings.reporting.top_n_samples_to_show


class ReportGenerator:
    @staticmethod
    def save_jsonl(results: List[Dict[str, Any]], output_path: str) -> None:
        """Save detailed results to JSONL format."""
        jsonl_path = output_path.replace(".csv", ".jsonl")
        try:
            with open(jsonl_path, "w", encoding="utf-8") as f:
                for entry in results:
                    clean_entry = {
                        k: (None if pd.isna(v) else v) for k, v in entry.items()
                    }
                    f.write(json.dumps(clean_entry, ensure_ascii=False) + "\n")
            logger.info(f"JSONL logs saved to {jsonl_path}")
        except Exception as e:
            logger.error(f"Failed to save JSONL: {e}", exc_info=True)

    @staticmethod
    def log_summary(df: pd.DataFrame) -> None:
        """Logs summary statistics to the console."""
        if df.empty or "e2e_latency_ms" not in df.columns:
            logger.warning("No data to summarize.")
            return

        valid = df[df["e2e_latency_ms"].notnull()]

        def print_stats(name: str, series: pd.Series) -> None:
            if series.empty:
                return
            data_list = series.dropna().tolist()
            if not data_list:
                return
            stats = MetricsCalculator.calculate_percentiles(data_list)
            logger.info(f"=== {name} ===")
            logger.info(
                f"  Mean: {stats['mean']:.2f} | "
                f"p50: {stats['p50']:.2f} | p95: {stats['p95']:.2f}"
            )

        print_stats("E2E Latency (ms)", valid["e2e_latency_ms"])
        if "ttft_ms" in valid.columns:
            print_stats("TTFT (ms)", valid["ttft_ms"])
        if "otps" in valid.columns:
            print_stats("OTPS (tokens/s)", valid["otps"])

        if "is_compliant" in df.columns:
            comp_series = df["is_compliant"].astype(float)
            compliance_rate = comp_series.mean() * 100
            logger.info(f"=== Compliance Rate: {compliance_rate:.1f}% ===")

        if "word_count_delta" in df.columns:
            avg_delta = df["word_count_delta"].mean()
            logger.info(f"=== Avg Word Delta: {avg_delta:+.1f} ===")

    @staticmethod
    def generate_comparison_report(
        df_map: Dict[str, pd.DataFrame], output_path: str
    ) -> None:
        """Generates a comprehensive comparison report."""
        md_path = output_path.replace(".csv", "_comparison.md")

        try:
            with open(md_path, "w", encoding="utf-8") as f:
                f.write("# Strategy Comparison Report\n\n")

                # --- 1. Performance Metrics ---
                f.write("## 1. Speed & Throughput (Performance)\n\n")
                f.write("| Strategy | TTFT (ms) | E2E (ms) | OTPS | Samples |\n")
                f.write("|---|---|---|---|---|\n")

                for strategy, df in df_map.items():
                    if not df.empty:
                        ttft = df["ttft_ms"].mean() if "ttft_ms" in df.columns else 0
                        e2e = df["e2e_latency_ms"].mean()
                        otps = df["otps"].mean() if "otps" in df.columns else 0
                        count = len(df)

                        f.write(
                            f"| **{strategy}** | {np.nan_to_num(ttft):.0f} | "
                            f"{np.nan_to_num(e2e):.0f} | {np.nan_to_num(otps):.1f} | {count} |\n"
                        )

                # --- 2. Quality & Cost Metrics ---
                f.write("\n## 2. Quality & Cost Efficiency\n\n")
                f.write(
                    "| Strategy | Compliance % | First-Try % | Avg Words | Delta | Avg Cost (Out) | Avg Attempts |\n"
                )
                f.write("|---|---|---|---|---|---|---|\n")

                for strategy, df in df_map.items():
                    if not df.empty:
                        comp_rate = df["is_compliant"].astype(float).mean() * 100

                        # First attempt compliance logic
                        if (
                            "first_attempt_compliant" in df.columns
                            and df["first_attempt_compliant"].notnull().any()
                        ):
                            first_try = (
                                df["first_attempt_compliant"].astype(float).mean() * 100
                            )
                        else:
                            # For A/B, if compliant, it's first try
                            first_try = comp_rate

                        avg_words = df["response_word_count"].mean()
                        avg_delta = (
                            df["word_count_delta"].mean()
                            if "word_count_delta" in df.columns
                            else 0
                        )

                        avg_cost = (
                            df["total_cost_output_tokens"].mean()
                            if "total_cost_output_tokens" in df.columns
                            else df["output_tokens"].mean()
                        )
                        avg_attempts = (
                            df["num_attempts"].mean()
                            if "num_attempts" in df.columns
                            else 1.0
                        )

                        f.write(
                            f"| **{strategy}** | **{np.nan_to_num(comp_rate):.1f}%** "
                            f"| {np.nan_to_num(first_try):.1f}% | "
                            f"{np.nan_to_num(avg_words):.1f} | {np.nan_to_num(avg_delta):+.1f} | "
                            f"{np.nan_to_num(avg_cost):.1f} | {np.nan_to_num(avg_attempts):.1f} |\n"
                        )

                # --- 3. Infrastructure Metrics ---
                f.write("\n## 3. Infrastructure Stability\n\n")
                f.write(
                    "| Strategy | Server Latency (ms) | "
                    "Client Overhead (ms) | Avg Stalls | Cache Hit (Tokens) |\n"
                )
                f.write("|---|---|---|---|---|\n")

                for strategy, df in df_map.items():
                    if not df.empty:
                        server = (
                            df["server_latency_ms"].mean()
                            if "server_latency_ms" in df.columns
                            else 0
                        )
                        overhead = (
                            df["client_overhead_ms"].mean()
                            if "client_overhead_ms" in df.columns
                            else 0
                        )
                        stalls = (
                            df["stall_count"].mean()
                            if "stall_count" in df.columns
                            else 0
                        )
                        cache_read = (
                            df["cache_read_input_tokens"].sum()
                            if "cache_read_input_tokens" in df.columns
                            else 0
                        )

                        f.write(
                            f"| **{strategy}** | {np.nan_to_num(server):.0f} | "
                            f"{np.nan_to_num(overhead):.0f} | "
                            f"{np.nan_to_num(stalls):.1f} | {cache_read} |\n"
                        )

                # --- 4. Per-Prompt Compliance ---
                f.write("\n## 4. Per-Prompt: Word Count & Compliance\n\n")

                all_ids = []
                for df in df_map.values():
                    if not df.empty:
                        all_ids.extend(df["prompt_id"].tolist())
                unique_ids = list(dict.fromkeys(all_ids))

                header = (
                    "| Prompt ID | "
                    + " | ".join([f"{s} (Words)" for s in df_map.keys()])
                    + " |\n"
                )
                separator = "|---|" + "---| " * len(df_map) + "\n"
                f.write(header + separator)

                for pid in unique_ids:
                    row = f"| {pid} | "
                    vals = []
                    for strategy in df_map.keys():
                        df = df_map[strategy]
                        match = df[df["prompt_id"] == pid]
                        if not match.empty:
                            words = match.iloc[0]["response_word_count"]
                            is_comp = match.iloc[0]["is_compliant"]
                            icon = "✅" if is_comp else "⚠️"
                            vals.append(f"{icon} {words}")
                        else:
                            vals.append("-")
                    row += " | ".join(vals) + " |\n"
                    f.write(row)

                # --- 5. Per-Prompt Latency ---
                f.write("\n## 5. Per-Prompt: E2E Latency (ms)\n\n")

                header = (
                    "| Prompt ID | "
                    + " | ".join([f"{s}" for s in df_map.keys()])
                    + " |\n"
                )
                f.write(header + separator)

                for pid in unique_ids:
                    row = f"| {pid} | "
                    vals = []
                    for strategy in df_map.keys():
                        df = df_map[strategy]
                        match = df[df["prompt_id"] == pid]
                        if not match.empty:
                            lat = match.iloc[0]["e2e_latency_ms"]
                            vals.append(f"{lat:.0f}")
                        else:
                            vals.append("-")
                    row += " | ".join(vals) + " |\n"
                    f.write(row)

            logger.info(f"Comparison report saved to {md_path}")
        except Exception as e:
            logger.error(f"Failed to generate comparison report: {e}")

    @staticmethod
    def generate_markdown_report(df: pd.DataFrame, output_path: str) -> None:
        """Generate a readable Markdown report with metrics and sample outputs."""
        md_path = output_path.replace(".csv", ".md")

        try:
            with open(md_path, "w", encoding="utf-8") as f:
                f.write("# Single Strategy Report\n\n")

                if not df.empty:
                    count = len(df)
                    ttft_avg = df["ttft_ms"].mean() if "ttft_ms" in df.columns else 0
                    e2e_avg = (
                        df["e2e_latency_ms"].mean()
                        if "e2e_latency_ms" in df.columns
                        else 0
                    )
                    otps_avg = df["otps"].mean() if "otps" in df.columns else 0
                    comp_rate = (
                        df["is_compliant"].astype(float).mean() * 100
                        if "is_compliant" in df.columns
                        else 0
                    )
                    overhead_avg = (
                        df["client_overhead_ms"].mean()
                        if "client_overhead_ms" in df.columns
                        else 0
                    )
                    server_avg = (
                        df["server_latency_ms"].mean()
                        if "server_latency_ms" in df.columns
                        else 0
                    )
                    stalls_avg = (
                        df["stall_count"].mean() if "stall_count" in df.columns else 0
                    )

                    # NEW: Extended single-strategy metrics
                    avg_delta = (
                        df["word_count_delta"].mean()
                        if "word_count_delta" in df.columns
                        else 0
                    )
                    first_try = (
                        df["first_attempt_compliant"].astype(float).mean() * 100
                        if "first_attempt_compliant" in df.columns
                        else 100.0
                    )

                    # Cost metrics
                    avg_cost_out = (
                        df["total_cost_output_tokens"].mean()
                        if "total_cost_output_tokens" in df.columns
                        else df["output_tokens"].mean()
                    )
                    avg_attempts = (
                        df["num_attempts"].mean()
                        if "num_attempts" in df.columns
                        else 1.0
                    )

                    f.write("## Summary Metrics\n")
                    f.write("| Metric | Value |\n|---|---|\n")
                    f.write(f"| **Samples** | {count} |\n")
                    f.write(
                        f"| **Compliance Rate** | **{np.nan_to_num(comp_rate):.1f}%** |\n"
                    )
                    f.write(
                        f"| **First-Try Success** | {np.nan_to_num(first_try):.1f}% |\n"
                    )
                    f.write(
                        f"| **Avg Word Delta** | {np.nan_to_num(avg_delta):+.1f} |\n"
                    )
                    f.write(f"| **Avg OTPS** | {np.nan_to_num(otps_avg):.1f} tok/s |\n")
                    f.write(f"| **Avg TTFT** | {np.nan_to_num(ttft_avg):.0f} ms |\n")
                    f.write(f"| **Avg E2E** | {np.nan_to_num(e2e_avg):.0f} ms |\n")
                    f.write(f"| Avg Attempts | {np.nan_to_num(avg_attempts):.1f} |\n")
                    f.write(
                        f"| Avg Cost (Out Tokens) | {np.nan_to_num(avg_cost_out):.1f} |\n"
                    )
                    f.write(
                        f"| Server Latency | {np.nan_to_num(server_avg):.0f} ms |\n"
                    )
                    f.write(
                        f"| Client Overhead | {np.nan_to_num(overhead_avg):.0f} ms |\n"
                    )
                    f.write(f"| Avg Stalls | {np.nan_to_num(stalls_avg):.2f} |\n")
                    f.write("\n")

                # Detailed Samples
                f.write(f"## Detailed Samples (Top {TOP_N_SAMPLES_TO_SHOW})\n")
                samples_to_show = df.head(TOP_N_SAMPLES_TO_SHOW)

                for idx, row in samples_to_show.iterrows():
                    response_text = str(row.get("response", ""))
                    is_comp = row.get("is_compliant", False)
                    status_icon = "✅" if is_comp else "⚠️"
                    attempts = row.get("num_attempts", 1)
                    is_est = row.get("is_estimated_usage", False)
                    est_mark = " *(est)*" if is_est else ""

                    f.write(f"### Sample {idx+1} {status_icon}\n")
                    f.write(
                        f"- **Words:** {row.get('response_word_count', 0)} "
                        f"(Target: 8-12)\n"
                    )
                    f.write(f"- **Attempts:** {attempts}\n")
                    f.write(
                        f"- **Metrics:** TTFT={row.get('ttft_ms', 0):.0f}ms, "
                        f"E2E={row.get('e2e_latency_ms', 0):.0f}ms, "
                        f"OTPS={row.get('otps', 0):.1f}{est_mark}\n"
                    )
                    f.write(f"- **Stop Reason:** `{row.get('stop_reason', 'N/A')}`\n")

                    f.write("<details>\n<summary>Prompt</summary>\n\n")
                    f.write(f"> {row.get('prompt', '')}\n")
                    f.write("</details>\n\n")

                    f.write("```text\n" + response_text + "\n```\n")
                    f.write("---\n")

            logger.info(f"Markdown report saved to {md_path}")

        except Exception as e:
            logger.error(f"Failed to save Markdown report: {e}", exc_info=True)
