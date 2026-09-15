# AWS EC2 Deployment Guide

## Quick Deploy (Manual)

### 1. Launch EC2 Instance
- Go to AWS Console → EC2 → Launch Instance
- Choose Amazon Linux 2023 (AMI: ami-0c02fb55956c7d316)
- Instance type: t3.small (free tier eligible)
- Create/select a key pair
- Security Group: allow ports 22 (SSH), 80 (HTTP), 443 (HTTPS), 8000 (API)

### 2. Connect via SSH
```bash
ssh -i your-key.pem ec2-user@YOUR_EC2_IP
```

### 3. Install Docker and run
```bash
sudo yum update -y
sudo yum install -y docker git curl
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ec2-user
```

### 4. Clone and deploy
```bash
cd /home/ec2-user
git clone https://github.com/Rishi12318/email_recommendation_chatbot_extension.git
cd email-recommendation

# Set environment variables
cat > .env << 'EOF'
GROQ_API_KEY=your_key
HF_TOKEN=your_token
GOOGLE_CLIENT_ID=your_client_id
EOF

# Build and run
docker compose up -d --build
```

### 5. Verify
```bash
curl http://localhost:8000/health
# Should return: {"status":"ok"}
```

## CloudFormation Deploy

```bash
aws cloudformation create-stack \
  --stack-name email-recommender \
  --template-body file://cloudformation.yaml \
  --parameters ParameterKey=InstanceType,ParameterValue=t3.small \
               ParameterKey=KeyPairName,ParameterValue=your-key-pair \
  --capabilities CAPABILITY_IAM
```

## Security Group Rules

| Port | Protocol | Source | Purpose |
|------|----------|--------|---------|
| 22 | TCP | Your IP | SSH access |
| 80 | TCP | 0.0.0.0/0 | HTTP (redirect to HTTPS) |
| 443 | TCP | 0.0.0.0/0 | HTTPS (production) |
| 8000 | TCP | 0.0.0.0/0 | FastAPI (testing only) |

**Note:** In production, use a reverse proxy (nginx) with SSL termination on port 443.
