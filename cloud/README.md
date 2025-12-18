# Cloud & Infrastructure

This section contains **production-grade cloud and infrastructure practices** for deploying ML- and AI-powered services.

The focus is on **reproducible deployments**, **clear architecture**, and **real-world operational concerns**, not cloud theory.

---

## ☁️ AWS

### Deploying FastAPI on AWS ECS (Fargate)
**Location**: [`aws/ecs/`](./aws/ecs/README.md)  
**Scope**: Containerized deployment of FastAPI services on AWS ECS  
**Includes**:
- ECS (Fargate) + ECR
- Application Load Balancer
- Health checks
- CI/CD with GitHub Actions
- Gunicorn + Uvicorn workers  

**Use cases**:
- Backend services
- AI / Bedrock service layers
- Production REST APIs
