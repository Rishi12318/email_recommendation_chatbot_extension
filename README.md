# AI Email Reply Browser Extension

Chrome extension that provides AI-powered email reply recommendations using a RAG pipeline with DistilBERT classification and FAISS semantic search, deployed on AWS.

## Architecture

```
Chrome Extension
       |
  User opens email
       |
       v
 "Recommend Reply"
       |
       v
  HTTPS request
       |
       v
  AWS EC2 / Docker
       |
       v
  FastAPI /api/recommend
       |
  +---------+----------+
  v                    v
RAG Pipeline      User/Email
DistilBERT          Context
  + FAISS
  |
  v
Recommendation
       |
       v
Chrome Extension
```

## Features

- **Reply Recommendations** - Generates contextual reply suggestions based on email content
- **Email Classification** - Classifies emails into 7 categories (deadline, interview, news, etc.)
- **RAG Pipeline** - Finds similar past emails using FAISS semantic search
- **LLM Integration** - Uses Groq LLM for natural replies, falls back to templates
- **Chrome Extension** - Extracts email text from Gmail, displays recommendations
- **Dockerized** - Containerized backend for consistent deployment
- **AWS Deployed** - EC2 with Docker, CloudFormation IaC, IAM best practices
- **CI/CD** - GitHub Actions: test -> build Docker -> deploy to AWS

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| Frontend | Chrome Extension (Manifest V3), JavaScript |
| Backend | Python 3.11, FastAPI, Uvicorn |
| AI/ML | DistilBERT, Sentence Transformers, FAISS, RAG |
| LLM | Groq SDK (llama-3.1-8b-instant) |
| Cloud | AWS EC2, IAM, Security Groups, SSM |
| DevOps | Docker, docker-compose, GitHub Actions |
| Testing | Pytest, Postman |

## Project Structure

```
email-recommendation/
├── app/
│   ├── main.py                    # FastAPI with /api/recommend endpoint
│   ├── core/prompts.py            # LLM prompts
│   └── services/
│       ├── classifier.py          # DistilBERT email classifier
│       ├── rag.py                 # FAISS semantic search + Groq LLM
│       ├── agent_rag.py           # Orchestrates classifier + RAG
│       └── local_responder.py     # Template-based replies (no LLM needed)
├── email_extension/               # Chrome Extension
│   ├── manifest.json
│   ├── popup.html / popup.js / popup.css
│   ├── content.js
│   └── icons/
├── aws/
│   ├── ec2-user-data.sh           # EC2 bootstrap script
│   ├── cloudformation.yaml        # AWS CloudFormation IaC template
│   └── DEPLOY.md                  # AWS deployment guide
├── tests/
│   ├── test_api.py                # API endpoint tests (11 tests)
│   └── test_services.py           # Service unit tests (11 tests)
├── Dockerfile                     # Containerized backend
├── docker-compose.yml             # Local/production Docker setup
├── .github/workflows/ci.yml      # CI/CD pipeline
├── Jenkinsfile                    # Jenkins CI/CD pipeline
├── requirements.txt
└── .env
```

## Quick Start

### 1. Run Locally

```bash
git clone https://github.com/Rishi12318/email_recommendation_chatbot_extension.git
cd email_recommendation_chatbot_extension
python -m venv .venv
.venv\Scripts\activate
pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt
python -m uvicorn app.main:app --reload
```

API available at: http://localhost:8000

### 2. Run with Docker

```bash
docker compose up -d
```

### 3. Install Chrome Extension

1. Open `chrome://extensions/` -> Enable Developer mode
2. Click "Load unpacked" -> Select `email_extension/`
3. Set API URL in extension popup (default: `http://localhost:8000`)

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/recommend` | **Get reply recommendation for an email** |
| `POST` | `/api/chat` | Chat with the email assistant |
| `POST` | `/api/emails/ingest` | Ingest emails into the RAG index |

### POST /api/recommend

```bash
curl -X POST http://localhost:8000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{"email": "Hi, can we schedule a meeting tomorrow?"}'
```

Response:
```json
{
  "recommendation": "Thanks for reaching out. I'm available for a meeting. Please share a few time slots that work for you, and I'll confirm.",
  "category": "other",
  "similar_emails": 3
}
```

## AWS Deployment

### Option A: Manual EC2

```bash
# SSH into EC2
ssh -i key.pem ec2-user@YOUR_IP

# Clone and run
git clone https://github.com/Rishi12318/email_recommendation_chatbot_extension.git
cd email_recommendation_chatbot_extension
docker compose up -d --build
```

### Option B: CloudFormation

```bash
aws cloudformation create-stack \
  --stack-name email-recommender \
  --template-body file://aws/cloudformation.yaml \
  --parameters ParameterKey=KeyPairName,ParameterValue=your-key \
  --capabilities CAPABILITY_IAM
```

See [`aws/DEPLOY.md`](aws/DEPLOY.md) for detailed instructions.

## CI/CD

**GitHub Actions** (`/.github/workflows/ci.yml`):
- On push: run tests (Python 3.11/3.12 matrix)
- On main: build Docker image, test container, deploy to AWS EC2

**Jenkins** (`Jenkinsfile`):
- Stages: Lint -> Test -> Build -> Deploy
- Slack notifications on success/failure

## Running Tests

```bash
pytest tests/ -v
```

22 tests covering API endpoints and services.

## Model Performance

| Metric | Score |
|--------|-------|
| Accuracy | 79.12% |
| F1 Weighted | 82.66% |
| ROC-AUC | 94.78% |

## Skills Demonstrated

| Area | Details |
|------|---------|
| **Python/FastAPI** | REST API with `/api/recommend`, `/api/chat`, `/api/emails/ingest` |
| **AI/ML** | DistilBERT classifier, FAISS vector search, RAG pipeline, LLM integration |
| **Chrome Extension** | Manifest V3, content scripts for Gmail email extraction |
| **AWS** | EC2 deployment, IAM, Security Groups, CloudFormation IaC, SSM |
| **Docker** | Multi-stage Dockerfile, docker-compose, containerized deployment |
| **CI/CD** | GitHub Actions (test->build->deploy), Jenkins pipeline |
| **APIs** | RESTful API design, OpenAPI docs, JSON request/response |
| **Infrastructure as Code** | CloudFormation templates, render.yaml, Jenkinsfile |
| **Cloud Security** | .env secrets, IAM roles, CORS policy, OAuth 2.0 |
| **Testing** | Pytest with 22 tests, mocked ML dependencies |
