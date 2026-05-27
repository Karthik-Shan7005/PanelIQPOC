from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from query_engine import process_question
from prompt_advisor import get_suggestions

# Initialize FastAPI app
app = FastAPI(
    title="PanelIQ API",
    description="AI-powered market research panel analytics",
    version="1.0.0"
)

# Allow React frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server
        "http://localhost:3000",   # Alternative React port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class QuestionRequest(BaseModel):
    question: str

class SuggestionRequest(BaseModel):
    partial: str

# ─── ENDPOINTS ────────────────────────────────────────────

@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "ok",
        "tool": "PanelIQ",
        "version": "1.0.0",
        "message": "Panel Intelligence API is running"
    }

@app.post("/ask")
async def ask(req: QuestionRequest):
    """
    Main endpoint — takes natural language question,
    returns SQL, data, summary, chart recommendation.
    """
    if not req.question or not req.question.strip():
        return {
            "success": False,
            "error": "Question cannot be empty.",
            "summary": "Please ask a question about your panel data."
        }

    result = process_question(req.question.strip())
    return result

@app.post("/suggest")
async def suggest(req: SuggestionRequest):
    """
    Returns 3 prompt suggestions as user types.
    Called with debouncing from frontend.
    """
    suggestions = get_suggestions(req.partial)
    return {"suggestions": suggestions}

@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "ok",
        "database": "KpiReports",
        "ai_model": "claude-sonnet-4-20250514",
        "module": "Engagement POC"
    }