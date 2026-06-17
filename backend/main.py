import json
import os
import sys

# Redirect stdout/stderr to a log file when running as a packaged exe
if getattr(sys, 'frozen', False):
    log_dir = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'PanelIQ', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    _log_file = open(os.path.join(log_dir, 'backend.log'), 'a', buffering=1)
    sys.stdout = _log_file
    sys.stderr = _log_file

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from query_engine import process_question, process_question_stream
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
    allow_origins=["*"],
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

@app.post("/ask/stream")
async def ask_stream(req: QuestionRequest):
    """Streaming endpoint — yields SSE events as the pipeline progresses."""
    if not req.question or not req.question.strip():
        async def _empty():
            yield f"data: {json.dumps({'type': 'error', 'content': 'Question cannot be empty.'})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        return StreamingResponse(_empty(), media_type="text/event-stream")

    async def _stream():
        try:
            async for event in process_question_stream(req.question.strip()):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        _stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


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


if __name__ == '__main__':
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8000)
    args, _ = parser.parse_known_args()

    uvicorn.run(app, host='127.0.0.1', port=args.port, log_level='error')