#!/bin/bash
# EC2 User Data script - runs on instance launch
# Installs Docker, clones repo, builds and runs the container

set -e

# Update system
yum update -y

# Install Docker
yum install -y docker
systemctl start docker
systemctl enable docker
usermod -aG docker ec2-user

# Install git
yum install -y git

# Install curl for healthchecks
yum install -y curl

# Clone the repository
cd /home/ec2-user
git clone https://github.com/Rishi12318/email_recommendation_chatbot_extension.git email-recommendation
cd email-recommendation

# Create .env file (set these via AWS Systems Manager Parameter Store in production)
cat > .env << 'EOF'
GROQ_API_KEY=your_groq_api_key_here
HF_TOKEN=your_hf_token_here
GOOGLE_CLIENT_ID=your_google_client_id_here
EOF

# Build and run with docker-compose
docker compose up -d --build

echo "Email Recommendation API is running on port 8000"
