# LangGraph Latency & Streaming Benchmark

## Goal
Establish a benchmark implementation for running **LangGraph agents** to evaluate flexibility, latency, and streaming capabilities.

The primary focus is on:
1.  **Stateful Agent Execution:** Implementing a `StateGraph` with persistent memory (checkpointers) to manage conversation history.
2.  **Streaming & Latency Analysis:** Measuring Time to First Token (TTFT), End-to-End (E2E) latency, and Inter-Token Latency (ITL) using LangChain's streaming protocols.
3.  **Infrastructure:** Using AWS Bedrock (via `langchain-aws`) as the LLM backend.

## Methodology

### 1. Dataset: MT-Bench Prompts
We utilize the **MT-Bench Prompts** dataset (`./data/mtbench_prompts.parquet`) to simulate realistic user inputs. The prompts are processed and categorized to measure performance across different complexity levels:

*   **Low Complexity:** Category `writing` or length < 50 tokens.
*   **Medium Complexity:** Categories `roleplay`, `reasoning` or length 50–100 tokens.
*   **High Complexity:** Multi-turn prompts, `math`, `coding`, or length > 100 tokens.

### 2. Metrics
To properly evaluate the performance, we measure specific latency metrics:

*   **TTFT (Time to First Token):** Time from request submission to the arrival of the first response chunk.
*   **E2E Latency (End-to-End):** Total time to receive the full response.
*   **TPS (Tokens Per Second):** eneration speed based on model usage metadata. Calculated as `Output Tokens / (E2E - TTFT)`.
*   **ITL (Inter-Token Latency):** Average time per token, calculated using official token counts from AWS metadata.
*   **Metadata:** Captures `input_tokens` and `output_tokens` directly from AWS Bedrock for 100% accuracy (via `messageStop` event or LangChain metadata).
*   **Percentiles (p50, p95, p99):** Measuring "unlucky" cases under concurrency.

### 3. Benchmarking Engine
The benchmark script utilizes `asyncio` to send concurrent requests to the LangGraph agent, simulating multiple users interacting simultaneously.

## Project Structure

```
.
├── data/
│   └── mtbench_prompts.parquet   # Source dataset
├── measurements/                 # Output reports (CSV, JSONL, Markdown)
├── src/
│   ├── baseline_raw.py           # Raw aioboto3 implementation (Baseline)
│   ├── langchain_aws_benchmark.py # Direct LangChain AWS implementation
│   ├── benchmark.py              # Main execution logic
│   ├── data_loader.py            # Dataset ingestion and categorization
│   ├── agent.py                  # LangGraph definition
│   ├── graph_adapter.py          # Adapter for streaming measurements
│   ├── metrics.py                # Statistical calculations
│   ├── reporting.py              # Report generation
│   ├── utils.py                  # Shared utilities (Parsing, UTC Time, Paths)
├── config.py                     # Pydantic settings
├── main.py                       # CLI Entry point
└── .env                          # Environment variables
```

## Setup

**1. Install Dependencies**
Using [uv](https://github.com/astral-sh/uv) package manager:
```sh
uv sync
```

**2. Configure Credentials**
Create a \`.env\` file in the project root:
```ini
# .env
AWS_ACCESS_KEY_ID="YOUR_ACCESS_KEY"
AWS_SECRET_ACCESS_KEY="YOUR_SECRET_KEY"
AWS_REGION="us-east-1"

# Logging
LOGGING_LEVEL="INFO"
BOTO3_LOGGING=false
```

## Usage

Run the benchmark using the CLI:

```sh
# Run LangGraph mode (default)
uv run python main.py --limit 5 --concurrency 2

# Run all modes (LangGraph, LangChain AWS, Raw Baseline) + Comparison report
uv run python main.py --mode all --limit 5 --concurrency 2

# Run specific modes
uv run python main.py --mode baseline
uv run python main.py --mode langchain_aws

# Custom input/output
uv run python main.py --data data/mtbench_prompts.parquet --output measurements/my_test.csv
```

## Outputs

Results are organized in the `measurements/` directory:
*   `measurements/langgraph/` - Results from standard LangGraph agent.
*   `measurements/langchain_aws/` - Results from direct LangChain AWS calls.
*   `measurements/baseline/` - Results from raw `aioboto3` calls.
*   `measurements/comparison/` - Summary reports comparing all modes (generated in `all` mode).

Each run generates:
1.  **CSV:** Raw metrics for each prompt.
2.  **JSONL:** Full request/response logs.
3.  **Markdown:** Human-readable report with sample dialogues.

> **See [RESEARCH_SUMMARY.md](./RESEARCH_SUMMARY.md) for the final analysis and conclusions derived from the benchmark runs.**

## Links

* [https://docs.langchain.com/oss/python/langgraph/overview](https://docs.langchain.com/oss/python/langgraph/overview)

## Research Findings & Methodology

### 1. Baseline Latency (No Framework at All) - "Speed ​​of Light"
*   **Goal:** Measure the pure latency of a Bedrock model without any frameworks or wrappers.
*   **Testing**: Direct AWS Bedrock API calls via `aioboto3`.
*   **Purpose:** Understand the minimum possible latency (TTFT) for a given model.

### 2. LangChain Wrapper Overhead (`aioboto3` vs. `langchain-aws`)
*   **Goal:** Measure the additional latency introduced by the LangChain wrapper (ChatBedrock).
*   **Testing:** Comparison of `aioboto3` (raw) vs `ChatBedrock`.
*   **Purpose:** Determine if the convenience of LangChain is worth the performance cost.

### 3. LangGraph Framework Overhead
*   **Goal:** Measure the overhead of LangGraph's state management and orchestration.
*   **Testing:** Comparing `ChatBedrock` (direct) vs `ChatBedrock` inside a `StateGraph`.
*   **Purpose:** Evaluate the "cost" of using a stateful agent framework.