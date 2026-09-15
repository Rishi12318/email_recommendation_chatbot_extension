#!/bin/bash
# Push Docker image to AWS ECR
# Usage: ./scripts/push-to-ecr.sh

set -e

REGION="ap-south-1"
REPO_NAME="email-recommendation"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URL="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"
IMAGE_TAG="${1:-latest}"

echo "=== Step 1: Login to ECR ==="
aws ecr get-login-password --region $REGION | \
  docker login --username AWS --password-stdin $ECR_URL

echo "=== Step 2: Create ECR repo (if not exists) ==="
aws ecr describe-repositories --repository-names $REPO_NAME 2>/dev/null || \
  aws ecr create-repository --repository-name $REPO_NAME --region $REGION

echo "=== Step 3: Build Docker image ==="
docker build -t $REPO_NAME:$IMAGE_TAG .

echo "=== Step 4: Tag image ==="
docker tag $REPO_NAME:$IMAGE_TAG $ECR_URL/$REPO_NAME:$IMAGE_TAG

echo "=== Step 5: Push to ECR ==="
docker push $ECR_URL/$REPO_NAME:$IMAGE_TAG

echo ""
echo "=== Done! ==="
echo "Image: $ECR_URL/$REPO_NAME:$IMAGE_TAG"
echo ""
echo "Next: Update k8s/deployment.yaml with this image path"
echo "Then run: kubectl apply -f k8s/"
