import json
import os
import sys
from pathlib import Path

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
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from query_engine import process_question, process_question_stream
from prompt_advisor import get_suggestions

app = FastAPI(
    title="Panel-IQ API",
    description="AI-powered market research panel analytics",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    question: str

class SuggestionRequest(BaseModel):
    partial: str

# ─── ENDPOINTS ────────────────────────────────────────────

@app.post("/ask")
async def ask(req: QuestionRequest):
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
    suggestions = get_suggestions(req.partial)
    return {"suggestions": suggestions}

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "database": "KpiReports",
        "ai_model": "claude-sonnet-4-20250514",
        "module": "Engagement POC"
    }

# ─── Serve React frontend (must be mounted last) ──────────────────────────────

def _frontend_path() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS) / 'frontend'
    return Path(__file__).parent.parent / 'frontend' / 'dist'

_fp = _frontend_path()
if _fp.exists():
    app.mount("/", StaticFiles(directory=str(_fp), html=True), name="frontend")


if __name__ == '__main__':
    import argparse
    import threading
    import time
    import webbrowser
    import uvicorn

    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--no-browser', action='store_true')
    args, _ = parser.parse_known_args()

    if not args.no_browser:
        def _open_browser():
            time.sleep(2)
            webbrowser.open(f'http://127.0.0.1:{args.port}')
        threading.Thread(target=_open_browser, daemon=True).start()

    uvicorn.run(app, host='127.0.0.1', port=args.port, log_level='error')
