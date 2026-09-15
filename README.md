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
| Deployment | Render.com |

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
│   │   └── build_pipeline.py      # End-to-end: data → preprocess → index
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
│   ├── test_api.py                # API endpoint tests
│   └── test_services.py           # Service unit tests
├── requirements.txt
├── pyproject.toml
├── render.yaml
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

## API Endpoints

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

## Deployment (Render)

The project includes a `render.yaml` for one-click deployment. The build process:
1. Installs CPU-only PyTorch and dependencies
2. Downloads a base DistilBERT model via `scripts/setup_model.py`
3. Starts with `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## Troubleshooting

- **Server won't start**: Check port 8000 isn't in use, verify `.env` has valid keys
- **Model not found**: The server auto-downloads a base model on first start; for accurate predictions, train with `python app/train/train_model.py`
- **Extension not working**: Reload in `chrome://extensions/`, check console (F12)
- **Gmail OAuth issues**: Ensure redirect URI `http://localhost:8000/api/gmail/callback` is configured in Google Cloud Console
