# Amazon Bedrock Workshop

Hands-on implementation guide for building production-ready AI applications with AWS Bedrock foundation models.

## 🚀 Overview
Practical exploration of AWS Bedrock capabilities through structured examples and real-world use cases. This workshop demonstrates how to leverage state-of-the-art foundation models (Claude, Llama, Titan) for various AI applications.

## 📁 Contents

### [`Building Chatbots with AWS Bedrock.ipynb`](./01_text_and_core_generation.ipynb)
**Hands-on guide covering:**
- **Text Summarization**: Using both Invoke and Converse APIs
- **Model Flexibility**: Easy switching between foundation models
- **Multi-turn Conversations**: Building contextual dialogues
- **Streaming Responses**: Real-time content delivery with ConverseStream API
- **Code Generation**: Using LLMs to generate functional code
- **Function Calling**: Integrating external tools for weather data retrieval

## 🔧 Prerequisites

```bash
# AWS Configuration
aws configure
# Or set environment variables:
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_DEFAULT_REGION="us-east-1"
```

# Python Dependencies
pip install boto3 jupyter ipykernel