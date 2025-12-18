# Foundations

This directory contains **core foundations for machine learning and modern AI systems**.
It is structured by **levels of abstraction**, from mathematics to frameworks and foundation models.
Each subdirectory represents a focused knowledge domain with executable code and concrete implementations.

---

## Foundation Models & LLM Internals

### LLM / Transformer Fundamentals
**Location**: [`llm_fundamentals/`](./llm_fundamentals/README.md)  
**Scope**: Core building blocks of modern LLMs  
**Coverage**:
- Scaled Dot-Product Attention
- Multi-Head Attention
- Masking semantics and API contracts
- PyTorch-aligned implementations  
**Purpose**: Understand *how* LLMs work internally, not just how to call them

---

## Deep Learning Frameworks

### PyTorch Coding Challenges
**Location**: [`pytorch-coding-challenges/`](./pytorch-coding-challenges/README.md)  
**Scope**: Low-level PyTorch implementation practice  
**Coverage**:
- Custom CNNs and RNNs from scratch
- Parameter initialization
- Shape tracing and failure modes  
**Purpose**: Fluency with `nn.Module` and production-grade debugging

### TensorFlow / Keras — Production & Scale
**Location**: [`tensorflow-official-tutorials/`](./tensorflow-official-tutorials/README.md)  
**Scope**: Production-oriented deep learning and large-scale training  
**Coverage**:
- Distributed training strategies
- Model serialization and deployment
- TensorBoard and experiment tracking
- Hyperparameter tuning with Keras Tuner
- Multi-domain workflows (vision, NLP, time series)  
**Purpose**: Understand TensorFlow as an end-to-end production ML framework

### PyTorch - Core & Internals
**Location**: [`pytorch-official-tutorials/`](./pytorch-official-tutorials/README.md)  
**Scope**: Core PyTorch mechanics and training workflows  
**Coverage**:
- Autograd & backprop
- Custom datasets and dataloaders
- Training loops and optimization  
**Purpose**: Framework-level mastery and debugging competence

---

## Cloud AI Platforms

### Amazon Bedrock
**Location**: [`amazon-bedrock-workshop/`](./amazon-bedrock-workshop/README.md)  
**Scope**: Managed foundation models on AWS  
**Coverage**:
- Prompt engineering
- Streaming & function calling
- Multi-modal workflows
- Cost-aware inference  
**Purpose**: Bridge between model internals and production AI systems

---

## 🧠 Core Domains

### Classical Machine Learning (Yandex Handbook)
**Location**: [`yandex_handbook_rus/`](./yandex_handbook_rus/README.md)  
**Scope**: End-to-end classical ML pipeline  
**Coverage**:
- EDA & preprocessing
- Metrics and loss functions
- Linear & non-linear models
- Cross-validation & pipelines  
**Purpose**: Strong baseline intuition before deep learning and LLMs

### Mathematical Foundations
**Location**: [`theory/`](./theory/README.md)  
**Scope**: Probability theory, combinatorics, linear algebra, mathematical statistics
**Coverage**:
- Discrete & continuous distributions
- Conditional probability & Bayes theorem
- Expectation, variance, covariance
- Combinatorial reasoning  
**Purpose**: Formal grounding for ML models, metrics, and uncertainty reasoning

---

## 🎯 Objectives of This Section

- Build **first-principles understanding** of ML and LLM systems
- Master framework-level APIs and failure modes
- Connect mathematical theory with executable implementations
- Treat models as systems, not black boxes
- Prepare a solid base for MLOps and production deployment
