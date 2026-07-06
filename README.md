Overview
Email Recommendation System is an AI-powered email assistant that helps users manage their inbox. It uses a fine-tuned DistilBERT model to classify emails into categories, detects deadlines and expirations, and provides intelligent recommendations through a conversational interface.

The system consists of:

A FastAPI backend that serves the AI model and API endpoints

A Chrome extension that provides the user interface

A RAG (Retrieval-Augmented Generation) pipeline for intelligent responses

Features
Email Classification
Classifies emails into 7 categories: deadline, interview_call, news, confirmation_email, otp, expired_email, other

Uses DistilBERT fine-tuned on a combination of real and synthetic email data

Achieves 79% accuracy on validation set

Smart Recommendations
Detects deadlines and expiration dates

Recommends actions: delete, archive, keep, remind

Groups similar emails for bulk actions

Conversation Interface
Chat-based interaction through the browser extension

Natural language queries like "Show me emails from Amazon"

Context-aware responses using RAG pipeline

User Profile Based Filtering
Users specify if they are a student or working professional

Work emails are identified based on sender domain (.edu for students, company domains for professionals)

Reduces false positives in email categorization

Tech Stack
Backend
FastAPI for API endpoints

DistilBERT for email classification

FAISS for vector search

Groq LLM for natural language responses

Sentence Transformers for text embeddings

Frontend
Chrome Extension (HTML, CSS, JavaScript)

Chrome Storage API for user settings

Training
Hugging Face Transformers

PyTorch

Scikit-learn

Project Structure
text
email-recommendation/
├── app/
│   ├── main.py                    # FastAPI server
│   ├── core/
│   │   ├── config.py              # Configuration settings
│   │   └── prompts.py             # LLM prompts
│   ├── services/
│   │   ├── classifier.py          # Email classifier
│   │   ├── rag.py                 # RAG pipeline
│   │   └── llm_client.py          # Groq client
│   └── models/
│       └── email_classifier/      # Trained model
├── data/
│   ├── train.csv                  # Training data
│   └── val.csv                    # Validation data
├── email-extension/               # Chrome extension
│   ├── manifest.json
│   ├── popup.html
│   ├── style.css
│   ├── popup.js
│   ├── content.js
│   └── background.js
├── requirements.txt
├── .env.example
└── README.md
Installation
Prerequisites
Python 3.11 or higher

Node.js (for Chrome extension development, optional)

Chrome browser (for testing the extension)

Step 1: Clone the Repository
text
git clone https://github.com/yourusername/email-recommendation.git
cd email-recommendation
Step 2: Create Virtual Environment
text
python -m venv .venv
.venv\Scripts\activate
Step 3: Install Dependencies
text
pip install -r requirements.txt
Step 4: Set Up Environment Variables
Copy .env.example to .env and fill in your API keys:

text
cp .env.example .env
Edit .env file:

text
GROQ_API_KEY=your_groq_api_key
HF_TOKEN=your_huggingface_token
Step 5: Prepare Training Data
text
python data/prepare_data.py
Step 6: Train the Model (Optional - Model is already trained)
text
python train.py
Step 7: Run the Server
text
python -m uvicorn app.main:app --reload
The API will be available at: http://localhost:8000

Chrome Extension Installation
Step 1: Open Chrome Extensions Page
Open Chrome browser

Navigate to chrome://extensions/

Enable Developer mode (toggle in top right)

Step 2: Load the Extension
Click "Load unpacked"

Select the email-extension folder from the project

Step 3: Configure the Extension
Click the extension icon in the toolbar

Enter your name and email

Select your profession (Student or Working Professional)

Click "Save Settings"

Click "Connect Gmail" to authorize email access

API Endpoints
Health Check
text
GET /health
Response: {"status": "ok"}
Chat
text
POST /api/chat
Headers:
  X-Groq-Key: your_groq_api_key
Body:
  {
    "messages": [{"role": "user", "content": "Show me emails from Amazon"}]
  }
Response:
  {
    "reply": "Found 5 emails from Amazon...",
    "recommendations": [],
    "end_of_conversation": false
  }
User Profile
text
POST /api/user/profile
Body:
  {
    "name": "John Doe",
    "email": "john@example.com",
    "profession": "student"
  }
Response:
  {"message": "Profile saved successfully"}
Usage Examples
Search Emails
User: "Show me emails from Amazon"
Agent: "Found 5 emails from Amazon. 2 are order confirmations, 3 are promotional."

Delete Expired Emails
User: "Delete all expired emails"
Agent: "Found 12 expired emails. Delete them? (Yes/No)"

Set Reminder
User: "Remind me about the assessment deadline"
Agent: "I will remind you 2 days before the deadline."

Get Summary
User: "Summarize my recent emails"
Agent: "You have 8 emails from work, 3 from services, and 2 from educational institutions."

Model Performance
Metric	Score
Accuracy	79.12%
F1 Weighted	82.66%
ROC-AUC	94.78%
Top-2 Accuracy	85.60%
Per-Class Performance
Category	Precision	Recall	F1
deadline	1.000	1.000	1.000
interview_call	1.000	1.000	1.000
news	0.999	0.927	0.961
otp	0.988	0.995	0.991
other	0.998	0.592	0.744
expired_email	0.172	1.000	0.294
confirmation_email	1.000	0.074	0.139
Evaluation
Run evaluation on the validation set:

text
python evaluation/evaluate.py
Output:

Classification report

Confusion matrix plot (saved to evaluation/plots/)

Per-class metrics chart (saved to evaluation/plots/)

Metrics CSV (saved to evaluation/plots/)

Troubleshooting
Server Won't Start
Check if port 8000 is in use: netstat -ano | findstr :8000

Make sure all dependencies are installed

Verify .env file has correct API keys

Model Not Found
Run training first: python train.py

Or download pre-trained model

Extension Not Working
Reload the extension in chrome://extensions/

Check console for errors (F12)

Verify Gmail is connected

Gmail OAuth Issues
Ensure you have created OAuth credentials in Google Cloud Console

Add authorized redirect URI: http://localhost:8000/api/gmail/callback

Contributing
Fork the repository

Create a feature branch

Commit your changes

Push to the branch

Open a pull request