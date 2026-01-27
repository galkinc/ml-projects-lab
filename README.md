# ML / AI Engineering Knowledge Base

### 🎯 Foundations
Core mathematical, ML, deep learning, LLM, and cloud fundamentals.

-> [Foundations overview](./foundations/README.md)

Covers:
- Mathematical foundations (probability, statistics)
- Classical ML pipelines
- Deep learning frameworks (PyTorch, TensorFlow)
- LLM / Transformer internals
- Cloud AI platforms

### ☁️ Cloud & Infrastructure
Production-ready cloud and deployment practices for ML and AI systems.

-> [Cloud & Infrastructure](./cloud/README.md)

Focus:
- AWS ECS (Fargate)
- CI/CD for ML services
- FastAPI-based AI services
- Infrastructure reproducibility

### 🔬 Research & Experiments
Applied research, prototypes, and comparative analysis of AI/ML services and techniques.

*   [**LangGraph Latency & Streaming Benchmark**](./research/langgraph-latency-streaming-benchmark/README.md): The full analysis [aws_comprehend_analysis.md](./research/langgraph-latency-streaming-benchmark/RESEARCH_SUMMARY.md)
    *   Comparative analysis of LangGraph, LangChain, and raw `aioboto3` (AWS Bedrock) overhead.
    *   Focus on Time to First Token (TTFT), TPS, and E2E latency in streaming mode.
*   [**AWS Comprehend Medical Analysis**](./research/comprehend-medical-research/README.md): The full analysis [aws_comprehend_analysis.md](./research/comprehend-medical-research/aws_comprehend_analysis.md) 
    *   In-depth analysis of AWS Comprehend Medical APIs (`DetectEntitiesV2`, `InferICD10CM`, etc.).
    *   Use cases, limitations, and side-by-side output comparisons.
    *   A reusable, CLI-based framework for running reproducible experiments.

## 🛠 Technical Stack


- **Frameworks**: PyTorch, TensorFlow, Keras  
- **Cloud & AI**: AWS (ECS, Bedrock)  
- **Domains**: NLP, LLMs, Time Series, Computer Vision, Distributed Training  
- **Tooling**: Docker, GitHub Actions, Jupyter, AWS CLI
