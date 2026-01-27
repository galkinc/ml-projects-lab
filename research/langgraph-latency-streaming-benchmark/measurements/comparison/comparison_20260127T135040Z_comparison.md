# Benchmark Comparison Report

## Global Metrics Comparison

| Mode | Avg TTFT (ms) | Avg E2E (ms) | p95 E2E | Avg TPS | Samples |
|---|---|---|---|---|---|
| langgraph | 715.96 | 2511.52 | 2896.14 | 289.49 | 5 |
| baseline | 1061.72 | 2876.63 | 3263.50 | 308.14 | 5 |
| langchain_aws | 754.65 | 2481.67 | 3045.87 | 268.70 | 5 |


## Per-Prompt TTFT Comparison (ms)

| Prompt ID | langgraph | baseline | langchain_aws |
|---|---| ---| ---| 
| 44067482 | 541.12 | 1093.01 | 532.71 |
| 46091167 | 581.99 | 1018.05 | 1214.11 |
| 57239570 | 1347.47 | 1064.78 | 720.94 |
| 65106343 | 552.46 | 1091.08 | 602.23 |
| 25568812 | 556.79 | 1041.69 | 703.27 |
