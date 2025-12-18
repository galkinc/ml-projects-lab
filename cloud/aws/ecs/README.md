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

From [the AWS docs](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/getting-started-fargate.html?spm=a2ty_o01.29997173.0.0.7ecc517160RlCZ#prerequisites): "The security group you select when creating a service [...] must have port 80 open for inbound traffic.". So let us used 80 port instead 8080.

Make sure your Dockerfile is correct. 

Note that I use `uv` as a package manager, and my typical Dockerfile might look like this:

```dockerfile
FROM python:3.14-slim-bookworm

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONUNBUFFERED=True
ENV PYDEVD_DISABLE_FILE_VALIDATION=1
ENV UV_COMPILE_BYTECODE=1

COPY pyproject.toml uv.lock README.md ./

COPY ./main.py .
COPY ./app /app

RUN uv sync --locked

EXPOSE 80
ENV PATH="/.venv/bin:$PATH"

ENTRYPOINT ["gunicorn"]
CMD ["--bind", "0.0.0.0:80", "--workers", "1", "--worker-class", "uvicorn.workers.UvicornWorker", "--graceful-timeout", "30", "--timeout", "60", "main:app"
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
  - In the search bar at the top, enter ECR and select [Elastic Container Registry](https://us-east-1.console.aws.amazon.com/ecr/private-registry/repositories?region=us-east-1)

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
    - Repository name (for example: `ai-assistant`)
    - Repository URI (for example: `123456789.dkr.ecr.us-east-1.amazonaws.com/ai-assistant`)
    - Tabs: Created at, Tag immutability, Encryption type

- Step 4: Configure lifecycle policy (optional, but recommended)
    - Go to the created repository
    - "Lifecycle policies" tab → "Create policy"
    - Configure a rule to automatically remove old images:
    ```json
    {
     "rules": [
       {
         "rulePriority": 1,
         "description": "Keep last 30 images (enough for rollbacks)",
         "selection": {
           "tagStatus": "any",
           "countType": "imageCountMoreThan",
           "countNumber": 30
         },
         "action": {
           "type": "expire"
         }
       }
     ]
   } 
    ```
- Step 5: Create Task Execution Role
  1. Go to [IAM Console](https://us-east-1.console.aws.amazon.com/iam/home) -> [Roles](https://console.aws.amazon.com/iam/home#/roles) -> Create role
  2. Trusted entity: AWS service Custom trust policy
  3. Use case: Elastic Container Service -> Elastic Container Service Task (Allows ECS tasks to call AWS services on your behalf.) -> Next
  4. click 
  5. In the next step, add the built-in policies:
      - AmazonECSTaskExecutionRolePolicy - (required) grants ECR pull and CloudWatch logs permissions
      - AmazonBedrockFullAccess (or you could create a custom policy, because AmazonBedrockFullAccess in production can be overkill), AmazonS3ReadOnlyAccess, AWSXRayDaemonWriteAccess/AWSXRayWriteOnlyAccess - (optional) if permissions to Bedrock/S3, etc. are required.
  6. Add name, e.g. `ecsTaskExecutionRole` and description and check permissions. -> create role
    
- Step 6: [Task Definition](https://us-east-1.console.aws.amazon.com/ecs/v2/task-definitions) (create manually or via CLI):
  ```yaml
  {
    "family": "ai-assistant-task",
    "networkMode": "awsvpc",
    "requiresCompatibilities": ["FARGATE"],
    "cpu": "256",
    "memory": "512",
    "executionRoleArn": "arn:aws:iam::594541045873:role/ecsTaskExecutionRole",
    "taskRoleArn": "arn:aws:iam::594541045873:role/ecsTaskExecutionRole",
    "containerDefinitions": [
      {
        "name": "ai-assistant-container",
        "image": "placeholder",
        "portMappings": [{ "containerPort": 80 }],
        "essential": true,
        "logConfiguration": {
          "logDriver": "awslogs",
          "options": {
            "awslogs-group": "/ecs/ai-assistant-app",
            "awslogs-region": "us-east-1",
            "awslogs-stream-prefix": "ecs"
          }
        },
        "healthCheck": {
          "command": ["CMD-SHELL", ""curl -fs http://localhost:80/health >/dev/null || exit 1"],
          "interval": 30,
          "timeout": 5,
          "retries": 3,
          "startPeriod": 60
        }
      }
    ]
  }
  ```

- Step 7: Create a Cluster
  - [Go to ECS Console -> Clusters](https://us-east-1.console.aws.amazon.com/ecs/v2/clusters) -> Create cluster
  - Cluster name: `ai-assistant-cluster`
  - Infrastructure: AWS Fargate

- Step 8: Create a Service
  - Go to created cluster -> Services -> Create
  - Task Definition: `ai-assistant-task`
  - Service name: `ai-assistant-service`
  - Launch type: FARGATE
  - Networking
    -  default (or yours)
    -  be shure that 80 port is open in your security group

- Step 9: Create a log-group
  - open [CloudWatch](https://us-east-1.console.aws.amazon.com/cloudwatch)
  - create a log group `/ecs/ai-assistant-app`
  - optional: choosed retention in dayes equal 30 or month

- Step 10: Add secrets to GitHub
  Settings → Secrets and variables → Actions → New repository secret
    - AWS_ACCESS_KEY_ID
    - AWS_SECRET_ACCESS_KEY
    
- Step 11: Configure GitHub Actions workflow
  ```yaml
  name: Deploy to ECS

  on:
    push:
      branches: [main]
  
  env:
    AWS_REGION: us-east-1
    ECR_REPOSITORY: ai-assistant
    ECS_CLUSTER: ai-assistant-cluster
    ECS_SERVICE: ai-assistant-service
    TASK_DEFINITION_FAMILY: ai-assistant-task
    CONTAINER_NAME: ai-assistant-container  # <- container name in the task definition
  
  jobs:
    deploy:
      timeout-minutes: 30
      runs-on: ubuntu-latest
      steps:
        - name: Checkout
          uses: actions/checkout@v4
  
        - name: Configure AWS credentials
          uses: aws-actions/configure-aws-credentials@v4
          with:
            aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
            aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
            aws-region: ${{ env.AWS_REGION }}
  
        - name: Login to Amazon ECR
          id: login-ecr
          uses: aws-actions/amazon-ecr-login@v2
  
        - name: Build and push Docker image
          env:
            ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
            IMAGE_SHA: ${{ github.sha }}
          run: |
            docker build -t $ECR_REPOSITORY .
  
            # Immutable tag: commit SHA
            IMAGE_SHA_TAG="$ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_SHA"
            docker tag $ECR_REPOSITORY $IMAGE_SHA_TAG
            docker push $IMAGE_SHA_TAG
            echo "IMAGE_SHA_TAG=$IMAGE_SHA_TAG" >> $GITHUB_ENV
            echo "IMAGE_URL=$IMAGE_SHA_TAG" >> $GITHUB_ENV  # for jq
  
        - name: Download current task definition
          run: |
            aws ecs describe-task-definition \
              --task-definition $TASK_DEFINITION_FAMILY \
              --query 'taskDefinition' \
              --output json > task-definition.json
  
        - name: Update image in task definition
          env:
            IMAGE_URL: ${{ env.IMAGE_SHA_TAG }}
          run: |
            jq --arg IMAGE "$IMAGE_URL" \
               --arg CONTAINER_NAME "${{ env.CONTAINER_NAME }}" \
               '
                 (.containerDefinitions[] | select(.name == $CONTAINER_NAME)).image = $IMAGE
               ' \
               task-definition.json > updated-task-definition.json
  
        - name: Register new task definition revision
          id: register-task
          run: |
            RESPONSE=$(aws ecs register-task-definition \
              --cli-input-json file://updated-task-definition.json \
              --query 'taskDefinition.{family:family,revision:revision}' \
              --output json)
            
            echo "TASK_FAMILY=$(echo $RESPONSE | jq -r '.family')" >> $GITHUB_ENV
            echo "TASK_REVISION=$(echo $RESPONSE | jq -r '.revision')" >> $GITHUB_ENV
  
        - name: Update ECS service to use new task revision
          run: |
            aws ecs update-service \
              --cluster $ECS_CLUSTER \
              --service $ECS_SERVICE \
              --task-definition ${{ env.TASK_FAMILY }}:${{ env.TASK_REVISION }} \
              --force-new-deployment
  
        - name: Wait for service stability (optional but recommended)
          run: |
            aws ecs wait services-stable \
              --cluster $ECS_CLUSTER \
              --services $ECS_SERVICE
  ```

 - Step 12:
   - [Open Load Balancer](https://us-east-1.console.aws.amazon.com/ec2/home?region=us-east-1#LoadBalancers:) and chose "Create Load Balancer"
   - Chose "Application Load Balancer"
   - Settings:
     - Name: ai-assistant-alb
     - Scheme: internet-facing
     - IP address type: IPv4
     - VPC: yours VPC (default)
     - Availability Zones: chose 2+ zones
   - Define Target Group
     - Name: ai-assistant-tg
     - Target type: IP
     - Protocol: HTTP (HTTPS)
     - Port: 80
     - Health check path: /health or /docs
   - Update ECS Service
     - ECS → Clusters → your cluster → your service → Update service
     - Enable Load balancing section:
       - Add Load Ballancing
       - Load balancer type: Application Load Balancer
       - Select ALB: ai-assistant-alb
       - Listener: 80
       - Container name: port 80:80
       - Target group: ai-assistant-tg
     - Configure eregistration delay in ALB -> gunicorn graceful-timeout + 20 sec
     - Security Groups
       - Security Group ALB
         ```json
         {
           "Inbound": [
             { "Protocol": "HTTP", "Port": 80, "Source": "0.0.0.0/0" },
             { "Protocol": "HTTPS", "Port": 443, "Source": "0.0.0.0/0" }
           ],
           "Outbound": [
             { "Protocol": "All", "Port": "All", "Source": "0.0.0.0/0" }
           ]
         }
         ```
       - Security Group Tasks
       ```json
       {
         "Inbound": [
           { "Protocol": "HTTP", "Port": 80, "Source": "Security Group ALB" }
         ]
       }
       ```
 
 IAM Permissions for GitHub Actions (in secrets.AWS_ACCESS_KEY_ID and SECRET):
 ! resources `:YOUR-ACCOUNT:` - replace with a real AWS account ID:
 ```
  - "arn:aws:ecs:us-east-1:YOUR-ACCOUNT:service/ai-assistant-cluster/ai-assistant-service"
  + "arn:aws:ecs:us-east-1:123456789012:service/ai-assistant-cluster/ai-assistant-service"
 ```

 You can get the account ID via CLI: ```aws sts get-caller-identity --query Account --output text```


## Save configuration in your project git  
Recomendation to save all data in yourgit repo, it could be something like this:
```
your-ai-assistant/
├── .github/
│   └── workflows/
│       └── deploy-ecs.yml          ← ✅ your GitHub Actions workflow
│
├── infra/
│   ├── task-definition.json        ← ✅ original Task Definition (for manual import or CI)
│   └── ecr-lifecycle-policy.json   ← ✅ ECR policy (for reproducibility/IaC in the future)
│   └── deploy-manual.sh            ← ✅ CLI alternative to CI (for testing)
│
├── ops/
│   └── iam-policy-github-actions.json  ← ✅ IAM policy (for audit and recovery)
│
├── app/
│   ├── main.py                     ← your FastAPI code
│   ├── Dockerfile                  ← ✅ your docker file
│   └── requirements.txt
│
├── Dockerfile                      ← ✅ (alternative: symlink to app/Dockerfile or here)
├── README.md                       ← deployment documentation
└── .gitignore
```

---

## Links

* [Developer Guide: What is Amazon Elastic Container Service?](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/Welcome.html)
* [Workshop: Amazon ECS Immersion Day](https://catalog.workshops.aws/ecs-immersion-day/en-US)
* [Developer Guide: Learn how to create an Amazon ECS Linux task for Fargate](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/getting-started-fargate.html)
