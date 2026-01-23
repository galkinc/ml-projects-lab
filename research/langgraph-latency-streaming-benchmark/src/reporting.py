import json
import pandas as pd
import logging
from typing import Dict, Any, List
from src.metrics import MetricsCalculator

logger = logging.getLogger(__name__)

class ReportGenerator:
    @staticmethod
    def save_jsonl(results: List[Dict[str, Any]], output_path: str):
        """Save detailed results to JSONL format."""
        jsonl_path = output_path.replace(".csv", ".jsonl")
        try:
            with open(jsonl_path, "w", encoding="utf-8") as f:
                for entry in results:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            logger.info(f"JSONL logs saved to {jsonl_path}")
        except Exception as e:
            logger.error(f"Failed to save JSONL: {e}")

    @staticmethod
    def log_summary(df: pd.DataFrame):
        """Logs summary statistics to the console."""
        if df.empty or "e2e_latency_ms" not in df.columns:
            logger.warning("No data to summarize.")
            return

        valid = df[df["e2e_latency_ms"].notnull()]
        metrics = MetricsCalculator.calculate_percentiles(valid["e2e_latency_ms"].tolist())
        
        logger.info("=== Overall Latency Metrics (ms) ===")
        for k, v in metrics.items():
            logger.info(f"{k:<5}: {v:.2f}")

        logger.info("=== Metrics by Complexity ===")
        if "complexity" in df.columns:
            grouped = valid.groupby("complexity")["e2e_latency_ms"].describe(percentiles=[0.5, 0.95, 0.99])
            logger.info(f"\n{grouped}")

    @staticmethod
    def generate_comparison_report(df_map: Dict[str, pd.DataFrame], output_path: str):
        """Generates a comparison report between different modes."""
        md_path = output_path.replace(".csv", "_comparison.md")
        
        try:
            with open(md_path, "w", encoding="utf-8") as f:
                f.write("# Benchmark Comparison Report\n\n")
                
                f.write("## Global Metrics Comparison\n\n")
                f.write("| Mode | Avg TTFT (ms) | Avg E2E (ms) | Avg TPS | Samples |\n")
                f.write("|---|---|---|---|---|\n")
                
                for mode, df in df_map.items():
                    if not df.empty:
                        ttft = df["ttft_ms"].mean()
                        e2e = df["e2e_latency_ms"].mean()
                        tps = df.get("tps", pd.Series([0])).mean()
                        f.write(f"| {mode} | {ttft:.2f} | {e2e:.2f} | {tps:.2f} | {len(df)} |\n")
                
                f.write("\n\n## Per-Prompt TTFT Comparison (ms)\n\n")
                
                all_ids = []
                for df in df_map.values():
                    all_ids.extend(df["prompt_id"].tolist())
                unique_ids = list(dict.fromkeys(all_ids))

                f.write("| Prompt ID | " + " | ".join(df_map.keys()) + " |\n")
                f.write("|---|" + "|---" * len(df_map) + "|\n")

                for pid in unique_ids:
                    row = f"| {pid} | "
                    vals = []
                    for mode in df_map.keys():
                        df = df_map[mode]
                        v = df[df["prompt_id"] == pid]["ttft_ms"].values
                        vals.append(f"{v[0]:.2f}" if len(v) > 0 and v[0] is not None else "N/A")
                    row += " | ".join(vals) + " |\n"
                    f.write(row)

            logger.info(f"Comparison report saved to {md_path}")
        except Exception as e:
            logger.error(f"Failed to generate comparison report: {e}")

    @staticmethod
    def generate_markdown_report(df: pd.DataFrame, output_path: str):
        """Generate a readable Markdown report with metrics and sample outputs."""
        md_path = output_path.replace(".csv", ".md")
        
        try:
            with open(md_path, "w", encoding="utf-8") as f:
                # 1. Header & Summary
                f.write(f"# Benchmark Report\n\n")
                
                # Calculate summary stats
                if not df.empty and "e2e_latency_ms" in df.columns:
                    ttft_avg = df["ttft_ms"].mean() if "ttft_ms" in df.columns else 0
                    e2e_avg = df["e2e_latency_ms"].mean()
                    count = len(df)
                    
                    f.write("## Summary Metrics\n")
                    f.write(f"| Metric | Value |\n|---|---|\n")
                    f.write(f"| Total Samples | {count} |\n")
                    f.write(f"| Avg TTFT | {ttft_avg:.2f} ms |\n")
                    f.write(f"| Avg E2E Latency | {e2e_avg:.2f} ms |\n")
                    f.write("\n")

                # 2. Detailed Samples
                f.write("## Detailed Samples\n")
                
                # Show top 5 slowest and top 5 fastest, or just first N
                # Let's show all for small runs, or top 20 for large
                samples_to_show = df.head(20)
                
                for idx, row in samples_to_show.iterrows():
                    prompt_preview = str(row.get('prompt', ''))[:100] + "..." if len(str(row.get('prompt', ''))) > 100 else row.get('prompt', '')
                    response_preview = str(row.get('response', ''))
                    
                    f.write(f"### Sample {idx+1} (ID: {row.get('prompt_id')})\n")
                    f.write(f"- **Complexity:** {row.get('complexity')}\n")
                    f.write(f"- **TTFT:** {row.get('ttft_ms', 0):.2f} ms\n")
                    f.write(f"- **E2E:** {row.get('e2e_latency_ms', 0):.2f} ms\n")
                    f.write(f"- **TPS:** {row.get('tps', 0):.2f}\n")
                    f.write(f"- **Tokens:** {row.get('output_tokens', 0)}\n\n")
                    
                    f.write("<details>\n<summary><strong>Prompt</strong></summary>\n\n")
                    f.write(f"```text\n{row.get('prompt', '')}\n```\n")
                    f.write("</details>\n\n")
                    
                    f.write("<details>\n<summary><strong>Response</strong></summary>\n\n")
                    f.write(f"```text\n{response_preview}\n```\n")
                    f.write("</details>\n\n")
                    f.write("---\n\n")

            logger.info(f"Markdown report saved to {md_path}")
            
        except Exception as e:
            logger.error(f"Failed to save Markdown report: {e}")
