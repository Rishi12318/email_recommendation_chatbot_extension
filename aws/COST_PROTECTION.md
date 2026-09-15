# AWS Account & Cost Protection Setup

## Step 1: Check Your Region

Always use a region close to you. For free tier, use **us-east-1** (N. Virginia).

```bash
# Set default region
aws configure set default.region us-east-1

# Verify
aws configure get default.region
```

## Step 2: Enable Free Tier Usage Alerts

1. Go to **AWS Console** -> **Billing** -> **Billing Preferences**
2. Check **Receive Free Tier Usage Alerts**
3. Enter your email
4. Save

## Step 3: Set Up a Budget ($10/month cap)

```bash
# Deploy the budget template
aws cloudformation create-stack \
  --stack-name cost-protection \
  --template-body file://budgets.yaml \
  --capabilities CAPABILITY_IAM
```

Or manually:
1. Go to **AWS Console** -> **Billing** -> **Budgets**
2. Click **Create budget**
3. Choose **Cost budget**
4. Set monthly limit: **$10**
5. Add alert at **80%** ($8) -> your email
6. Create

## Step 4: Check Free Tier Eligibility

Go to: https://console.aws.amazon.com/billing/home#/freetier

This shows what you've used vs what's free.

## Step 5: EC2 Instance for This Project

Use **t3.micro** or **t3.small** (both free tier eligible for 750 hours/month).

```bash
# Launch a free-tier EC2 instance
aws ec2 run-instances \
  --image-id ami-0c02fb55956c7d316 \
  --instance-type t3.micro \
  --key-name your-key-pair \
  --security-group-ids sg-xxxxx \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=EmailRecommender}]'
```

## Cost Estimate for This Project

| Resource | Monthly Cost | Free Tier? |
|----------|-------------|------------|
| EC2 t3.micro | ~$0 (750 hrs) | Yes |
| EBS 8GB | ~$0 (30 GB) | Yes |
| Data Transfer | ~$0 (< 100GB) | Yes |
| **Total** | **~$0/month** | |

## Quick Sanity Check Before Deploying

```bash
# 1. Check your current spend
aws ce get-cost-and-usage \
  --time-period Start=2026-09-01,End=2026-09-15 \
  --granularity MONTHLY \
  --metrics "UnblendedCost"

# 2. List your running instances (check for forgotten resources)
aws ec2 describe-instances \
  --query "Reservations[].Instances[].{ID:InstanceId,Type:InstanceType,State:State.Name}" \
  --output table

# 3. Check active budgets
aws budgets describe-budgets --account-id $(aws sts get-caller-identity --query Account --output text)
```
