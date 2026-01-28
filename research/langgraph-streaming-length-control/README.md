# Research: LangGraph Streaming Length Control

## 1. Context & Motivation
This project is a derivative of `langgraph-latency-streaming-benchmark`. 

**The Challenge:**
In conversational AI, responses often vary wildly in length (200+ tokens vs desired 10-20), affecting both User Experience (UX) and system latency. We need to constrain response length to ~8-12 words ("Brief Mode") while maintaining a streaming interface.

**The Nuance on Performance:**
Previous benchmarks (`comparison_20260127T135846Z`) demonstrated that well-optimized frameworks (`langchain-aws`) and properly implemented raw clients achieve comparable TTFT (~665-675ms). 
*Key Insight:* The choice to use raw `aioboto3` here is driven by the need for **fine-grained control** over the generation stream (e.g., instant interruption, token counting), which is difficult to achieve through high-level abstractions, rather than pure raw speed.

**The Conflict:**
*   **Structured Output (Pydantic)** is often blocking and unsuitable for low-latency streaming.
*   **High-level Abstractions** (like `ChatBedrock`) hide the event loop, making it harder to implement logic like "abort stream immediately if token count > X".
*   **Hard Cutoffs (`max_tokens`)** result in broken sentences.

**The Goal:**
Implement and benchmark strategies for length control within LangGraph. We will use `aioboto3` primarily for **control granularity** (access to raw stream chunks, ability to interrupt) rather than just assumed raw speed.

## 2. Hypotheses
1.  **Prompting vs. Logic:** Good prompt engineering with `StopSequences` is the fastest method but may have lower compliance accuracy than a logical loop.
2.  **The "Fast Loop" Theory:** We can implement a "Correction Loop" (Generate -> Check -> Regenerate if too long) inside LangGraph using raw `aioboto3`. We hypothesize that removing `ChatBedrock` overhead will make this loop fast enough to be viable, whereas standard LangChain components would make it too slow.
3.  **Streaming Interruption:** A custom stream handler that counts tokens and interrupts generation is the most efficient way to prevent massive "runaway" responses, acting as a safety net.

## 3. Implementation Strategies

We will compare three specific implementations suitable for streaming.

### Strategy A: The "Optimized Baseline" (Prompt + StopSeq)
*   **Mechanism:** Single node. System prompt instructs brevity ("8-12 words").
*   **Technical:** 
    *   Use `aioboto3` directly.
    *   Set `stopSequences` (e.g., `.` or `\n`) to encourage logical breaks.
    *   Set `maxTokens` to a safety buffer (e.g., ~30 tokens).
*   **Pros:** Lowest Latency (TTFT/E2E).
*   **Cons:** No guarantee of strict length; model might ignore instructions.

### Strategy B: The "Stream Monitor" (Soft Cutoff)
*   **Mechanism:** Single node. Streaming logic actively counts tokens/words.
*   **Technical:** 
    *   Custom `StreamWriter` logic inside the node.
    *   If `token_count > limit`: Issue `stream.close()` or stop yielding.
*   **Pros:** Guaranteed upper bound on latency and cost.
*   **Cons:** Potential for cut-off sentences (bad UX), though mitigated by monitoring logical stops (sentence boundaries).

### Strategy C: The "Fast Correction Loop" (Agentic Repair)
*   **Mechanism:** Multi-node Graph (`Generate` -> `Evaluate` -> `Retry`).
*   **Technical:** 
    *   **Node 1 (Generate):** Streams result using `aioboto3`.
    *   **Node 2 (Evaluate):** Python function checks word count.
    *   **Edge:** If `length > 12` AND `attempt < 2`: Route to Retry. Else: END.
    *   *Crucial Detail:* Since we are optimizing for speed, we use raw clients inside nodes, bypassing `langchain-aws`.
*   **Pros:** High quality/compliance.
*   **Cons:** High Latency Penalty (User waits for 2 generations if the first fails). *Note: For streaming, this implies we might buffer the first attempt or the user sees the correction happening.* **Decision:** We will measure this as a "Buffered" approach to see the cost of guaranteed quality.

## 4. Architecture Changes

### `src/agent.py`
*   Move away from `ChatBedrock` initialization.
*   Implement `AsyncBedrockClient` wrapper (singleton) for raw usage.
*   Define a generic `GraphState` that supports tracking:
    *   `messages`: Conversation history.
    *   `token_count`: Accumulated usage.
    *   `attempt_count`: For loop control.

### `src/graph_adapter.py`
*   Update to handle multi-step generations.
*   **TTFT Metric:** Must measure from start of *first* attempt.
*   **E2E Metric:** Must measure until end of *final* attempt.

## 5. Metrics & Success Criteria

We will generate a new benchmark report comparing the strategies.

#### Primary Metrics

| Metric | Definition | Target |
|---|---|---|
| **Compliance Rate** | % of responses within 8-12 words | > 90% |
| **TTFT (Client)** | Time to First Token (ms) - perceived user latency | < 600ms |
| **E2E Latency** | Total generation time (ms) | Minimize |
| **Latency Penalty** | `E2E (Loop) - E2E (Baseline)` | Assess cost of quality |
| **OTPS** | Output Tokens Per Second (decoding speed, excl. TTFT) | Maximize |

#### Extended Metrics

| Metric | Definition | Purpose |
|---|---|---|
 **Server Latency** | Processing time reported by AWS (`metrics.latencyMs`) | Identify backend slowness |
| **Client Overhead** | `E2E - Server Latency` (Network + SDK cost) | Identify client/network bottlenecks |
| **Stall Count** | Number of inter-token pauses > 300ms | Detect "freezes" (bad UX) |
| **Inter-token Latency** | p99 latency between tokens | Smoothness of streaming |
| **Hit Token Limit** | % of responses stopped by `maxTokens` | Check if model was cut off |
| **Cache Hit Rate** | Input tokens read from cache | Verify prompt caching efficiency |
| **Word Count Delta** | `Actual Words - Target Center (10)` | Deviation from ideal length |
| **Retry Attempts** | Number of generation loops (Strategy C) | Cost of correction |
| **Cost Efficiency** | `Total Output Tokens / Valid Output Tokens` | "Price" of 1 valid token |
| **First Attempt Compliant** | % where Strategy C succeeded without retry | Efficiency of Strategy C |

## 6. Implementation Details & Caveats

### Strategy B: Token Estimation
Due to the streaming nature of `converse_stream`, `usage` metrics (token counts) are only sent by AWS in the final `metadata` event.
*   **The Issue:** When Strategy B forces a hard cutoff (via `break`), the stream is closed **before** the `metadata` event is received.
*   **The Fix:** In case of forced cutoff, `output_tokens` are estimated: `max(chunk_count, words * 1.3)`. `input_tokens` are unknown (recorded as 0).
*   **Indicator:** Results with estimated usage are marked with `is_estimated_usage=True` (internal flag) and `*(est)*` in reports. Consequently, OTPS for these samples is also an approximation.

### Strategy C: Cost Calculation
*   **OTPS (Throughput):** Calculated based on the **final** successful attempt only. This reflects the actual generation speed of the model.
*   **Total Cost:** Calculated as the sum of **all attempts** (initial + retries).
*   **Latency:** TTFT is measured from the start of the *first* attempt (user perception). E2E is measured until the end of the *last* attempt.

### Word vs Token Counting
*   Strategies targeting "8-12 words" use simple `len(text.split())` for compliance checking.
*   AWS Limits (`maxTokens`) are set to ~30 to provide a safety buffer, but logical control relies on words.

## 7. How to Run

### Installation
Ensure you have `uv` installed.
```bash
uv sync
```

### Running Benchmarks
The `main.py` script supports 4 modes via the `--strategy` argument:

1.  **Strategy A (Prompt Only):**
    ```bash
    uv run python research/langgraph-streaming-length-control/main.py --strategy a --limit 10
    ```
2.  **Strategy B (Stream Monitor):**
    ```bash
    uv run python research/langgraph-streaming-length-control/main.py --strategy b --limit 10
    ```
3.  **Strategy C (Fast Loop):**
    ```bash
    uv run python research/langgraph-streaming-length-control/main.py --strategy c --limit 10
    ```
4.  **All Strategies (Comparison):**
    Runs all three sequentially and generates a comparison report.
    ```bash
    uv run python research/langgraph-streaming-length-control/main.py --strategy all --limit 50 --concurrency 5
    ```

**Arguments:**
*   `--limit`: Number of prompts to process (0 for all ~80).
*   `--concurrency`: Number of parallel requests (default 5).

## 8. Reports & Analysis

### Output Location
All reports are generated in `research/langgraph-streaming-length-control/measurements/`.
*   Subfolders `strategy_a/`, `strategy_b/`, `strategy_c/` contain individual run logs.
*   `measurements/comparison_YYYYMMDD...md` contains the aggregated comparison.

### Understanding the Reports
*   **Performance:** Focus on **E2E Latency** and **OTPS**. Strategy B/C may be slower than A.
*   **Quality:** Look at **Compliance Rate**. B and C should be near 100%.
*   **Cost:** Look at **Avg Attempts** (C) and **Total Cost** (C will be higher).
*   **Warnings:** Look for `*(est)*` markers. This means token usage was estimated due to forced stream cutoff (Strategy B).

### Research Findings
For a summary of conclusions and insights, see [RESEARCH_SUMMARY.md](./RESEARCH_SUMMARY.md).
