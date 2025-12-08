# Deploying FastAPI Applications on AWS ECS

## 🎯 Introduction
[Amazon Elastic Container Service (ECS)](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/Welcome.html) is a fully managed container orchestrator from AWS.

### 🎯 What is this?
A guide to deploying FastAPI applications on Amazon Elastic Container Service (ECS).

### 🚀 Who is it for?
- Developers who need to deploy a FastAPI service
- Engineers deploying REST APIs in the cloud
- Anyone who wants to containerize a web application on AWS

### 💡 Use cases:
1. REST API service
2. Microservice with business logic
3. Service layer for AWS Bedrock
4. Web application on FastAPI

---

## 📋 Basic Plan
1. Preparing a Docker Image
2. Creating an ECR Repository
3. Configuring an ECS Cluster + Task Definition
4. Configuring an Application Load Balancer
5. Configuring Autodeployment (CI/CD)

### 1. Preparing a Docker Image
 
Make sure your Dockerfile is correct. 

Note that I use `uv` as a package manager, and my typical Dockerfile might look like this:

```dockerfile
FROM python:3.14-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONUNBUFFERED=True
ENV PYDEVD_DISABLE_FILE_VALIDATION=1
ENV UV_COMPILE_BYTECODE=1

COPY pyproject.toml uv.lock README.md ./

COPY ./main.py .
COPY ./app /app

RUN uv sync --locked

EXPOSE 8080
ENV PATH="/.venv/bin:$PATH"

ENTRYPOINT ["gunicorn"]
CMD ["--bind", "0.0.0.0:8080", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "main:app"]
```

### 2. Creating an ECR repository

There are two ways to create an ECR repository:
- by command console
- via the AWS Console (UI)

#### Create a repository by command console
```bash
# Create a repository
aws ecr create-repository --repository-name ai-assistant

# Authorization
aws ecr get-login-password --region your-region | docker login \
--username AWS \
--password-stdin your-account.dkr.ecr.your-region.amazonaws.com

# Build and push the image
docker build -t ai-assistant .
docker tag ai-assistant:latest your-account.dkr.ecr.your-region.amazonaws.com/ai-assistant:latest
docker push your-account.dkr.ecr.your-region.amazonaws.com/ai-assistant:latest
```

#### Create a repository by the AWS Console (UI)

- Step 1: Login to the AWS Console
  - Log in to the [AWS Console](https://aws.amazon.com/console/)
  - In the search bar at the top, enter ECR and select [Elastic Container Registry](https://us-east-1.console.aws.amazon.com/ecr/private-registry/repositories)

- Step 2: Create a repository
  1. Click the blue "Create repository" button
  2. Visibility settings:
    - Private: Only your account (recommended for production)
    - Public: Accessible to everyone (like Docker Hub)
  3. Repository settings:
    - Repository name: `ai-assistant`
    - Tag immutability: [✔] Enable - Each deployment is a new tag
      - Prevents accidental overwriting - the v1.0.0 tag will always point to the same image.
      - Deployment idempotency - if you deploy version 1.0.0, it will always be the same.
      - Rollback is easier - you know exactly which image you're rolling back to.
      - Security - no one can "replace" an existing tag.
  4. Access settings (IAM):
    - Leave the default settings for now
    - Can be configured later in the Permissions section
  5. Click "Create repository"

- Step 3: View the created repository. Once created, you will see:
   - Management buttons
   - Repository name (for example: ai-assistant)
   - Repository URI (for example: 123456789.dkr.ecr.us-east-1.amazonaws.com/ai-assistant)
   - Tabs: Created at, Tag immutability, Encryption type
---

## Links

* [Developer Guide: What is Amazon Elastic Container Service?](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/Welcome.html)
* [Workshop: Amazon ECS Immersion Day](https://catalog.workshops.aws/ecs-immersion-day/en-US)
* [Developer Guide: Learn how to create an Amazon ECS Linux task for Fargate](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/getting-started-fargate.html)
