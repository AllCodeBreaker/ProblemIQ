
import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from chat import Chat
from patterns import COMMON_PATTERNS

app = FastAPI()

templates = Jinja2Templates(directory="templates")

# Replace with your real GitHub repository URL
GITHUB_URL = "https://github.com/allCodeBreaker/ProblemIQ"

# Initialize Chat object
chat_bot = Chat()


@app.get(path="/", response_class=HTMLResponse)
def home(req: Request):
    preview_categories = dict(list(COMMON_PATTERNS.items())[:2])
    return templates.TemplateResponse(
        name="index.html",
        request=req,
        context={"aptitude_patterns": preview_categories, "all_aptitude_patterns": COMMON_PATTERNS, "github_url": GITHUB_URL}
    )


@app.get(path="/learn", response_class=HTMLResponse)
def learn_overview(req: Request):
    return templates.TemplateResponse(
        name="topic.html",
        request=req,
        context={"topic_name": "Learn", "page_title": "Learn all categories", "categories": COMMON_PATTERNS, "mode": "learn", "github_url": GITHUB_URL}
    )


@app.get(path="/practice", response_class=HTMLResponse)
def practice_overview(req: Request):
    return templates.TemplateResponse(
        name="topic.html",
        request=req,
        context={"topic_name": "Practice", "page_title": "Practice all categories", "categories": COMMON_PATTERNS, "mode": "practice", "github_url": GITHUB_URL}
    )


@app.get(path="/learn/{category_name}", response_class=HTMLResponse)
def learn_category(req: Request, category_name: str):
    category_name = category_name.lower()
    if category_name not in COMMON_PATTERNS:
        raise HTTPException(status_code=404, detail="Category not found")

    patterns = COMMON_PATTERNS[category_name]
    return templates.TemplateResponse(
        name="learn.html",
        request=req,
        context={"category_name": category_name, "patterns": patterns, "mode": "learn", "github_url": GITHUB_URL}
    )


@app.post("/api/chat")
async def chat_endpoint(req: Request):
    try:
        data = await req.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    question = (data.get("question") or "").strip()
    topic = (data.get("topic") or "General aptitude").strip()
    patterns = data.get("patterns") or []
    mode = (data.get("mode") or "teach").strip().lower()

    if not question:
        raise HTTPException(status_code=400, detail="Question is required")

    if mode == "quiz":
        quiz_data = chat_bot.quiz(question=question, topic=topic, patterns=patterns)
        return JSONResponse(content=quiz_data)
    else:
        return StreamingResponse(
            chat_bot.teach_stream(question=question, topic=topic, patterns=patterns),
            media_type="text/plain"
        )

