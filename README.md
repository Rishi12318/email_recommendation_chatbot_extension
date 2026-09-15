# Email Recommendation System

AI-powered email assistant that helps users manage their inbox. It uses a fine-tuned DistilBERT model to classify emails, detects deadlines and expirations, and provides intelligent recommendations through a conversational interface.

## Features

- **Email Classification** - Classifies emails into 7 categories: `deadline`, `interview_call`, `news`, `confirmation_email`, `otp`, `expired_email`, `other`
- **Smart Recommendations** - Detects deadlines, expiration dates, and recommends actions (delete, archive, keep, remind)
- **RAG Pipeline** - Semantic search over your emails using FAISS + Sentence Transformers
- **Conversational AI** - Chat-based interaction via Groq LLM or local template responses
- **Chrome Extension** - Gmail integration with Google OAuth and DOM scraping

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| Backend | FastAPI, Uvicorn, Pydantic |
| ML/AI | PyTorch, DistilBERT, Sentence Transformers, FAISS |
| LLM | Groq SDK (llama-3.1-8b-instant) |
| Gmail API | google-api-python-client, google-auth-oauthlib |
| Frontend | Chrome Extension (Manifest V3), vanilla JS |
| CI/CD | GitHub Actions, Jenkins |
| Deployment | Render.com (IaC via render.yaml) |
| Notifications | Slack, ServiceNow |

## APIs

The backend exposes a RESTful API built with **FastAPI**. Full API catalog: [`servicenow/api_catalog.json`](servicenow/api_catalog.json)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/chat` | Chat with the email assistant |
| `POST` | `/api/emails/ingest` | Ingest scraped emails into the index |
| `GET` | `/api/gmail/auth` | Start Gmail OAuth flow |
| `GET` | `/api/gmail/callback` | Gmail OAuth callback |
| `GET` | `/api/gmail/status` | Check Gmail connection status |
| `POST` | `/api/gmail/scan` | Fetch recent emails from Gmail |
| `POST` | `/api/gmail/index` | Index Gmail emails into FAISS |
| `GET` | `/api/gmail/emails` | List indexed emails |

### Example: Chat

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Show me emails from Amazon"}]}'
```

## Software Development Practices

| Practice | Implementation |
|----------|---------------|
| Version Control | Git with feature branch workflow |
| Code Review | Pull requests with CI gates |
| Testing | pytest with 18 unit/integration tests |
| CI/CD | GitHub Actions + Jenkins pipelines |
| Documentation | Auto-generated API catalog, README |
| Code Quality | Flake8 linting, type hints (Pydantic) |
| Environment Management | `.env` files, `requirements.txt`, `pyproject.toml` |

## Infrastructure as Code (IaC)

All infrastructure is defined declaratively:

- **`render.yaml`** - Render.com deployment: build commands, start command, env vars, Python version
- **`.github/workflows/ci.yml`** - GitHub Actions CI: Python matrix (3.11/3.12), install, test
- **`Jenkinsfile`** - Jenkins pipeline: lint, test, build, deploy stages with Slack notifications
- **`requirements.txt`** / **`pyproject.toml`** - Pinned dependency versions for reproducible builds

```yaml
# render.yaml - One-click deploy
services:
  - type: web
    name: email-assistant
    env: python
    buildCommand: pip install ... -r requirements.txt && python scripts/setup_model.py
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.12.11
```

## Infrastructure Automation

| Tool | Purpose |
|------|---------|
| **GitHub Actions** | Automated testing on push/PR, Python version matrix |
| **Jenkins** | Full pipeline: lint -> test -> build -> deploy |
| **Render.com** | Auto-deploy on push to main, environment variables |
| **Scripts** | `scripts/setup_model.py` auto-downloads model on first deploy |

## Jenkins Pipeline

Stages: Checkout -> Setup -> Install -> Lint -> Unit Tests -> Build Model -> Deploy

- Runs on every push and PR
- JUnit test reports published to Jenkins dashboard
- Slack notifications on success/failure
- Deploy stage triggers only on `main` branch

```groovy
stage('Unit Tests') {
    steps {
        sh 'pytest tests/ -v --junitxml=reports/test-results.xml'
    }
}
stage('Deploy to Render') {
    when { branch 'main' }
    steps { sh 'curl -X POST "${RENDER_DEPLOY_HOOK}"' }
}
```

## Slack Integration

- **Build notifications** - Slack alerts on CI build success/failure
- **Deploy notifications** - Slack alerts on Render deployment status
- **Slash commands** - `/email-search`, `/email-summary`, `/email-classify`
- Config: [`slack/app_config.json`](slack/app_config.json)

## ServiceNow Integration

- **API Catalog** - Full endpoint documentation in ServiceNow-compatible JSON: [`servicenow/api_catalog.json`](servicenow/api_catalog.json)
- **Change Management** - Deployments tracked as ServiceNow changes
- **Incident Management** - Health check endpoint for monitoring

## Cloud Security

| Practice | Implementation |
|----------|---------------|
| Secrets Management | `.env` files (git-ignored), Render env vars, Jenkins credentials |
| OAuth 2.0 | Google OAuth for Gmail API with scoped permissions |
| API Key Rotation | Environment variables, not hardcoded keys |
| CORS Policy | Restricted origins (localhost, chrome-extension, Render URL) |
| Dependency Scanning | Pinned versions in `requirements.txt` and `pyproject.toml` |
| No Secrets in Repo | `.gitignore` excludes `.env`, logs, model files |

## Project Structure

```
email-recommendation/
├── app/
│   ├── main.py                    # FastAPI application entry point
│   ├── core/
│   │   └── prompts.py             # LLM system prompt and RAG prompt template
│   ├── services/
│   │   ├── classifier.py          # DistilBERT email classifier wrapper
│   │   ├── rag.py                 # FAISS semantic search + Groq LLM
│   │   ├── agent_rag.py           # Orchestrates classifier + RAG
│   │   ├── gmail_auth.py          # Google OAuth2 flow
│   │   ├── gmail_service.py       # Gmail API email fetching
│   │   ├── local_responder.py     # Template-based responses (no LLM needed)
│   │   ├── build_rag_index.py     # Builds FAISS index from cleaned CSVs
│   │   └── build_pipeline.py      # End-to-end: data -> preprocess -> index
│   ├── data/
│   │   ├── data.py                # Training data generation
│   │   └── preprocesses.py        # Text cleaning for RAG indexing
│   ├── train/
│   │   └── train_model.py         # DistilBERT fine-tuning script
│   └── evaluation/
│       └── evaluation.py          # Model evaluation script
├── models/
│   ├── email_index.faiss          # FAISS vector index
│   ├── emails.json                # Email texts for RAG lookup
│   ├── index_meta.json            # Index metadata
│   └── email_classifier/         # Fine-tuned DistilBERT model
├── data/
│   ├── train.csv                  # Training data
│   ├── val.csv                    # Validation data
│   ├── train_cleaned.csv          # Cleaned for RAG
│   └── test_cleaned.csv           # Cleaned for RAG
├── email_extension/               # Chrome Extension
│   ├── manifest.json
│   ├── popup.html / popup.js
│   ├── style.css
│   ├── content.js
│   ├── background.js
│   └── gmail-api.js
├── scripts/
│   ├── setup_model.py             # Downloads base DistilBERT for deployment
│   └── colab_train.py             # Google Colab training script
├── tests/
│   ├── conftest.py                # Test mocks for heavy ML dependencies
│   ├── test_api.py                # API endpoint tests (7 tests)
│   └── test_services.py           # Service unit tests (11 tests)
├── .github/workflows/
│   └── ci.yml                     # GitHub Actions CI pipeline
├── slack/
│   └── app_config.json            # Slack bot config, webhooks, slash commands
├── servicenow/
│   └── api_catalog.json           # ServiceNow API catalog
├── Jenkinsfile                    # Jenkins CI/CD pipeline
├── requirements.txt
├── pyproject.toml
├── render.yaml                    # Infrastructure as Code (Render.com)
└── .env
```

## Installation

### Prerequisites

- Python 3.11 or higher
- Chrome browser (for the extension)

### Step 1: Clone and set up

```bash
git clone https://github.com/yourusername/email-recommendation.git
cd email-recommendation
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
```

### Step 2: Install dependencies

```bash
pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt
```

### Step 3: Set up environment variables

Create a `.env` file:

```
GROQ_API_KEY=your_groq_api_key      # Optional - uses local templates if not set
HF_TOKEN=your_huggingface_token      # Optional - for model downloads
GOOGLE_CLIENT_ID=your_client_id      # Optional - for Gmail OAuth
```

### Step 4: Run the server

```bash
python -m uvicorn app.main:app --reload
```

The API will be available at: http://localhost:8000

## Chrome Extension Installation

1. Open `chrome://extensions/` and enable **Developer mode**
2. Click **Load unpacked** and select the `email_extension/` folder
3. Click the extension icon, enter your details, and click **Connect Gmail**

## Running Tests

```bash
pytest tests/ -v
```

## Model Performance

| Metric | Score |
|--------|-------|
| Accuracy | 79.12% |
| F1 Weighted | 82.66% |
| ROC-AUC | 94.78% |
| Top-2 Accuracy | 85.60% |

### Per-Class F1

| Category | F1 Score |
|----------|----------|
| deadline | 1.000 |
| interview_call | 1.000 |
| otp | 0.991 |
| news | 0.961 |
| other | 0.744 |
| expired_email | 0.294 |
| confirmation_email | 0.139 |

## Evaluation

```bash
python -m app.evaluation.evaluation
```

Generates a classification report, confusion matrix, and per-class metrics charts in `evaluation/plots/`.

## Deployment

### Render.com (Production)

The project includes a `render.yaml` for one-click deployment:
1. Installs CPU-only PyTorch and dependencies
2. Downloads a base DistilBERT model via `scripts/setup_model.py`
3. Starts with `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Jenkins (On-Premise)

Pipeline stages: Checkout -> Setup -> Install -> Lint -> Test -> Build -> Deploy

```bash
# Trigger Jenkins build
curl -X POST http://jenkins:8080/job/email-assistant/build
```

### GitHub Actions (Cloud CI)

Automatic on push/PR to `main`/`master`:
- Python 3.11 + 3.12 matrix testing
- CPU-only PyTorch for fast CI
- JUnit test reports

## Troubleshooting

- **Server won't start**: Check port 8000 isn't in use, verify `.env` has valid keys
- **Model not found**: The server auto-downloads a base model on first start; for accurate predictions, train with `python app/train/train_model.py`
- **Extension not working**: Reload in `chrome://extensions/`, check console (F12)
- **Gmail OAuth issues**: Ensure redirect URI `http://localhost:8000/api/gmail/callback` is configured in Google Cloud Console
