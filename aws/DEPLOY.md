# AWS Deployment Guide (ECR + EKS)

## Prerequisites

Install on your laptop:
```bash
# AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip && sudo ./aws/install

# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# eksctl
curl --silent --location "https://github.com/eksctl-io/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin
```

Configure AWS CLI:
```bash
aws configure
# Enter: Access Key ID, Secret Access Key, Region (ap-south-1), Output (json)
```

## Step-by-Step Deployment

### Step 1: Create ECR Repository

```bash
aws ecr create-repository \
  --repository-name email-recommendation \
  --region ap-south-1
```

### Step 2: Login to ECR

```bash
aws ecr get-login-password --region ap-south-1 | \
  docker login --username AWS --password-stdin \
  YOUR_ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com
```

### Step 3: Build Docker Image

```bash
docker build -t email-recommendation .
docker images  # verify you see email-recommendation
```

### Step 4: Tag & Push to ECR

```bash
# Get your account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Tag
docker tag email-recommendation:latest \
  $ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com/email-recommendation:latest

# Push
docker push \
  $ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com/email-recommendation:latest
```

Or use the script:
```bash
chmod +x scripts/push-to-ecr.sh
./scripts/push-to-ecr.sh
```

### Step 5: Create EKS Cluster

```bash
eksctl create cluster \
  --name email-recommendation \
  --region ap-south-1 \
  --nodes 2 \
  --node-type t3.small
```

This takes ~15 minutes. It creates:
- 2 EC2 instances (t3.small)
- A managed Kubernetes control plane
- A load balancer

### Step 6: Configure kubectl

```bash
aws eks update-kubeconfig --region ap-south-1 --name email-recommendation
kubectl get nodes  # verify you see 2 nodes
```

### Step 7: Create Secrets

```bash
# Edit k8s/secrets.yaml with your actual API keys first
kubectl apply -f k8s/secrets.yaml
```

### Step 8: Deploy to Kubernetes

```bash
# Update k8s/deployment.yaml with your ECR image URL first
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

### Step 9: Get the Load Balancer URL

```bash
kubectl get services email-recommender-service
```

Look for `EXTERNAL-IP`. Your API is now at:
```
http://<EXTERNAL-IP>/health
http://<EXTERNAL-IP>/api/recommend
```

### Step 10: Update Chrome Extension

In `email_extension/popup.js` or the extension popup:
```
API URL: http://<EXTERNAL-IP>
```

## Verify Everything

```bash
# Check pods are running
kubectl get pods

# Check service
kubectl get svc

# Test the API
curl http://<EXTERNAL-IP>/health
curl -X POST http://<EXTERNAL-IP>/api/recommend \
  -H "Content-Type: application/json" \
  -d '{"email": "Can we schedule a meeting tomorrow?"}'
```

## Cleanup (to stop charges)

```bash
# Delete Kubernetes resources
kubectl delete -f k8s/service.yaml
kubectl delete -f k8s/deployment.yaml
kubectl delete -f k8s/secrets.yaml

# Delete EKS cluster (~15 min)
eksctl delete cluster --name email-recommendation --region ap-south-1

# Delete ECR repository
aws ecr delete-repository --repository-name email-recommendation --region ap-south-1 --force
```

## Architecture After Deployment

```
Chrome Extension
       |
   HTTPS request
       |
AWS Load Balancer (NLB)
       |
Kubernetes Service
       |
FastAPI Pod (x2 replicas)
       |
  +----+----+
  |         |
RAG     DistilBERT
FAISS   Classifier
```

## GitHub Secrets Required

| Secret | Description |
|--------|-------------|
| `AWS_ACCESS_KEY_ID` | IAM user access key |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret key |

## Resume

```
RAG-Based Email Recommendation System | GitHub | Live Demo
• Developed an AI-powered email recommendation system using Python, NLP,
  DistilBERT, PyTorch, Hugging Face, FAISS, semantic search and RAG.
• Containerized and deployed the FastAPI backend on AWS EKS using Docker
  and Kubernetes, with CI/CD automation through GitHub Actions and ECR.
• Built a Chrome extension integrating the deployed REST API for real-time
  email reply recommendations.
```
