# Agentic Learning Itinerary API (FastAPI)

Backend service that generates a **day-wise learning itinerary** (step-by-step plan) with **free resources only**.
Uses **OpenAI Responses API** with the built-in **web_search** tool and an optional server-side page fetch tool for verification.

## Features
- Day-wise itinerary (e.g., 7 days)
- Minimal links: 1–2 per day (configurable)
- Free-only enforcement: drops non-free/unknown links
- Agentic workflow: plan → search → (optional fetch) → verify → compose
- Swagger docs at `/docs`

## Setup

### 1) Create venv and install deps
```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2) Configure environment
Copy `.env.example` to `.env` and fill:
- `OPENAI_API_KEY`
- (optional) `OPENAI_MODEL` (default `gpt-4o-mini`)

### 3) Run
```bash
uvicorn app.main:app --reload --port 8000
```

Open:
- Health: http://127.0.0.1:8000/v1/health
- Docs:   http://127.0.0.1:8000/docs

## Generate an itinerary
POST `/v1/itinerary`

Example body:
```json
{
  "concept": "Agentic AI tool calling with OpenAI Responses API",
  "level": "beginner",
  "days": 7,
  "hours_per_day": 2,
  "prefer_format": "mix",
  "free_only": true
}
```

## Notes
- The response schema uses `url: str` (not `HttpUrl`) to avoid JSON Schema `format: uri` issues with structured output validators.
- The optional `fetch_page` tool is polite but basic. For production, add robots.txt compliance and stronger rate limiting.
