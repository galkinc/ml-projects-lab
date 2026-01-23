# Benchmark Comparison Report

## Global Metrics Comparison

| Mode | Avg TTFT (ms) | Avg E2E (ms) | Avg TPS | Samples |
|---|---|---|---|---|
| langgraph | 1604.51 | 3758.04 | 254.43 | 2 |
| baseline | 1319.46 | 3286.88 | 253.88 | 2 |
| langchain_aws | 1519.42 | 3006.90 | 267.31 | 2 |


## Per-Prompt TTFT Comparison (ms)

| Prompt ID | langgraph | baseline | langchain_aws |
|---||---|---|---|
| 44067482 | 1605.48 | 1632.66 | 1531.12 |
| 46091167 | 1603.53 | 1006.27 | 1507.72 |
