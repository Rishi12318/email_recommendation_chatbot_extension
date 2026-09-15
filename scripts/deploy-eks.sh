#!/bin/bash
# Create EKS cluster and deploy
# Usage: ./scripts/deploy-eks.sh

set -e

CLUSTER_NAME="email-recommendation"
REGION="ap-south-1"
NODES=2

echo "=== Step 1: Create EKS cluster ==="
echo "This takes ~15 minutes. Go grab a coffee."
eksctl create cluster \
  --name $CLUSTER_NAME \
  --region $REGION \
  --nodes $NODES \
  --node-type t3.small

echo "=== Step 2: Update kubeconfig ==="
aws eks update-kubeconfig --region $REGION --name $CLUSTER_NAME

echo "=== Step 3: Create secrets ==="
kubectl apply -f k8s/secrets.yaml

echo "=== Step 4: Deploy application ==="
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

echo "=== Step 5: Wait for Load Balancer ==="
echo "Waiting for external IP..."
sleep 30
kubectl get services email-recommender-service

echo ""
echo "=== Done! ==="
echo "Copy the EXTERNAL-IP from the output above"
echo "Update your Chrome extension API URL to: http://<EXTERNAL-IP>"
