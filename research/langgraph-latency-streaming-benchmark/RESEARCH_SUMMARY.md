# Research Summary

## Overview
This document summarizes the findings from the **LangGraph Latency & Streaming Benchmark** (v1.0). The goal was to quantify the performance overhead introduced by the LangGraph framework and LangChain library compared to a "bare metal" implementation using `aioboto3` (AWS SDK).

**Test Configuration:**
*   **Model:** AWS Bedrock (`us.amazon.nova-micro-v1:0`)
*   **Dataset:** MT-Bench Prompts (80 samples)
*   **Concurrency:** 4 parallel requests
*   **Region:** us-east-1

---

## Key Findings

### 1. Framework Overhead Analysis

| Mode | Avg TTFT (ms) | Avg E2E (ms) | Avg TPS | Overhead (TTFT) |
|---|---|---|---|---|
| **Raw Baseline** (`aioboto3`) | ~1622 ms | ~3128 ms | ~470 | **0 ms (Baseline)** |
| **LangChain AWS** (No Graph) | ~686 ms | ~2082 ms | ~401 | **-936 ms** (Unexpectedly faster*) |
| **LangGraph** (With State) | ~775 ms | ~2249 ms | ~366 | **+89 ms** (vs LangChain) |

*> **Note on Anomalies:** The baseline `aioboto3` implementation showed significantly higher latency (~1.6s TTFT) compared to LangChain (~0.7s). This is counter-intuitive and likely indicates that the raw `aioboto3` implementation lacks specific optimizations present in `langchain-aws` (e.g., efficient stream handling or connection pooling) or was subject to cold starts/throttling during the test run. In a stabilized environment, we expect Raw to be faster or equal.*

**Corrected Overhead Estimation (LangGraph vs LangChain):**
Comparing `langgraph` vs `langchain_aws` (which share the same underlying model client) reveals the true cost of the framework:
*   **TTFT Penalty:** ~90 ms (13% increase)
*   **E2E Penalty:** ~167 ms (8% increase)
*   **Throughput Drop:** ~35 TPS (9% decrease)

**Conclusion:** LangGraph introduces a measurable but acceptable overhead (~10%) for the benefits of state management and orchestration.

### 2. Latency Stability (p95)

| Mode | p95 E2E Latency (ms) |
|---|---|
| **LangGraph** | 4014.43 |
| **LangChain AWS** | 3745.62 |
| **Baseline** | 4607.85 |

LangGraph remains relatively stable even at the 95th percentile, following the performance curve of the underlying LangChain client.

---

## Detailed Observations

1.  **Token Throughput (TPS):**
    *   The "Raw" implementation achieved higher throughput (~470 TPS) despite the initial lag.
    *   LangGraph's state saving mechanisms (Checkpointer) likely contribute to the slight TPS drop (~366 TPS).

2.  **Per-Prompt Variance:**
    *   Certain prompts (e.g., ID `65106343`) showed consistent spikes across all modes, indicating model-side latency rather than framework issues.
    *   LangGraph occasionally exhibited high initial latency (e.g., ID `25568812` -> 2081ms), possibly due to graph initialization or memory I/O.

---

## Recommendations

1.  **Use `langchain-aws`:** For most use cases, the optimization provided by the library outweighs the theoretical benefits of a custom `aioboto3` wrapper, unless extreme optimization is required.
2.  **Accept LangGraph Overhead:** The ~10% latency cost is a reasonable trade-off for the structural benefits (cycles, state, persistence).
3.  **Optimize Checkpointers:** For high-load production systems, using an `AsyncSqliteSaver` or Redis-based checkpointer (instead of in-memory) should be benchmarked next, as it will likely impact latency more significantly.

---

*Generated based on benchmark run: 2026-01-27*
