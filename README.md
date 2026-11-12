# QuickCart – AI Customer Calling Agent

An AI-powered customer support assistant that simulates customer service calls through a web-based chat and voice interface.

The system uses a React frontend and FastAPI backend to handle customer queries, retrieve verified business information, and provide automated responses using Retrieval-Augmented Generation (RAG).

## Live Demo

- **Frontend:** https://ai-customer-calling-agent-ten.vercel.app
- **Backend API:** https://fvqj313t-fastapi-quickcart-ai-backend.apps-2.websson.cloud

## Features

- AI-powered customer support conversations.
- Browser-based voice input.
- Retrieval-Augmented Generation (RAG) using Sentence Transformers.
- FAQ-based knowledge retrieval.
- Business hours and store information queries.
- Order status lookup using order IDs.
- Human assistance request handling (simulated).
- Unknown-query fallback for unverified information.
- Configurable AI provider integration with Gemini and Groq fallback.
- PostgreSQL database integration.
- Conversation and API usage logging.

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | React, Vite |
| Backend | Python, FastAPI |
| AI / NLP | Sentence Transformers |
| Retrieval | RAG |
| AI Providers | Gemini, Groq |
| Database | PostgreSQL |
| Frontend Deployment | Vercel |
| Backend Deployment | Uppcoder |

## How It Works

1. A customer sends a message through the web interface or uses voice input.
2. The React frontend sends the request to the FastAPI backend.
3. The backend identifies the query intent.
4. The RAG system retrieves relevant information from the business knowledge base.
5. The AI provider generates an appropriate response when needed.
6. The assistant returns the response to the frontend.

## Example Queries

| Customer Query | Expected Function |
|---|---|
| What are your business hours? | Business information |
| What is your return policy? | FAQ retrieval |
| What is my order status for QC1001? | Order status lookup |
| Can I speak to a human agent? | Human assistance request |
| Random or unsupported question | Verified-information fallback |

## Return Policy

QuickCart's sample return policy:

- Returns are accepted within 7 days of delivery.
- Customers must contact support and provide their order ID.
- Approved refunds are processed within 5 business days.

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Backend health check |
| GET | `/faqs` | Retrieve FAQs |
| GET | `/business` | Retrieve business information |
| GET | `/orders/{order_id}` | Retrieve order details |
| POST | `/chat` | Process customer messages |
| POST | `/upload-document` | Upload knowledge-base documents |
| GET | `/documents` | List uploaded documents |
| DELETE | `/documents/{filename}` | Delete a document |

Interactive API documentation is available at `/docs` on the backend URL.

## Local Development

### Prerequisites

- Python 3.13+
- Node.js
- npm
- PostgreSQL

### Backend

From the project root:

```bash
python -m venv .venv
```

Activate the virtual environment on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Install the project's backend dependencies using its dependency file, then run:

```bash
uvicorn backend.main:app --reload --port 8000
```

Backend runs at:

`http://127.0.0.1:8000`

### Frontend

Navigate to the frontend directory:

```bash
npm install
npm run dev
```

Configure the frontend API base URL using:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Use the deployed backend URL when connecting to the production backend.

## Deployment

- **Frontend:** Deployed on Vercel.
- **Backend:** Deployed on Uppcoder.
- **Database:** PostgreSQL hosted with the Uppcoder stack.

Environment variables and API credentials must be configured securely in the respective deployment environments. Do not commit API keys, passwords, or database credentials to GitHub.

## Project Status

The application has a deployed frontend and backend. Core customer-support flows, FAQ retrieval, order status lookup, fallback responses, and return-policy retrieval have been tested.

## Author

**Amna Ahmed**

GitHub: [@amnak004](https://github.com/amnak004)

---
