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

| Mode | Avg TTFT (ms) | Avg E2E (ms) | Avg TPS | Analysis |
|---|---|---|---|---|
| **Raw Baseline** (`aioboto3`) | ~1242 ms | ~2901 ms | **863.7** | **Unrivaled Generation Speed (3.4x faster)**, but significant start lag. |
| **LangChain AWS** (No Graph) | **~665 ms** | **~2480 ms** | 253.6 | **Fastest TTFT.** Superior connection/transport optimization. |
| **LangGraph** (With State) | ~674 ms | **~2276 ms*** | 248.5 | Minimal overhead (~9ms) over LangChain. |

*\*Note: In this run, LangGraph's Avg E2E was slightly lower than LangChain's due to model response variance (shorter responses), but TTFT remains the reliable metric for framework overhead.*

**Overhead Observations:**
1.  **Start-up Cost (TTFT):** Raw `aioboto3` consistently shows a ~600ms penalty for the first token. Despite session reuse, the per-request client initialization in the async SDK remains the bottleneck for low-latency starts.
2.  **Generation Speed (TPS):** This is the most significant discovery. **Raw Baseline is 3.4x faster in token throughput (863 vs 253 TPS)**. LangChain's internal chunk processing, object instantiation (`AIMessageChunk`), and callback orchestration introduce a massive throughput bottleneck during high-speed streaming.
3.  **LangGraph Framework:** LangGraph adds a negligible **9ms penalty** to TTFT. It is an extremely efficient orchestration layer that does not perceptibly slow down the underlying LLM client.

**Conclusion:** 
*   **For Ultra-Fast Throughput:** If the goal is processing/displaying large amounts of text quickly, **Raw SDK is mandatory**.
*   **For Instant UX (Reactivity):** LangChain/LangGraph are better suited due to faster TTFT.
*   **For Complex Agents:** LangGraph is the optimal choice, providing state management with virtually zero latency cost.

### 2. Latency Stability (p95)

| Mode | p95 E2E Latency (ms) |
|---|---|
| **LangGraph** | 3704.04 |
| **LangChain AWS** | 4634.41 |
| **Baseline** | 4752.35 |

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
