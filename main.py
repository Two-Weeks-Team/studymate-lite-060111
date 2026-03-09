from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from routes import router as api_router

app = FastAPI(title="StudyMate Lite Backend", version="0.1.0")

app.include_router(api_router)

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", response_class=JSONResponse)
async def health_check():
    return {"status": "ok"}

# ---------------------------------------------------------------------------
# Root landing page – dark themed inline CSS
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def root():
    html_content = """
    <!DOCTYPE html>
    <html lang='en'>
    <head>
        <meta charset='UTF-8'>
        <title>StudyMate Lite API</title>
        <style>
            body {background:#121212;color:#e0e0e0;font-family:Arial,sans-serif;padding:2rem;}
            h1 {color:#ff9800;}
            a {color:#03a9f4;}
            .card {background:#1e1e1e;padding:1rem;border-radius:8px;margin-bottom:1rem;}
            .endpoint {margin-top:0.5rem;}
            .method {font-weight:bold;}
        </style>
    </head>
    <body>
        <h1>StudyMate Lite API</h1>
        <p>Instant flashcards from your notes – no accounts, no fees.</p>
        <div class='card'>
            <h2>Available Endpoints</h2>
            <div class='endpoint'>
                <span class='method'>GET</span> <a href='/health'>/health</a> – health check
            </div>
            <div class='endpoint'>
                <span class='method'>POST</span> <a href='/api/v1/generate'>/api/v1/generate</a> – generate flashcards from raw text
            </div>
            <div class='endpoint'>
                <span class='method'>POST</span> <a href='/api/v1/study'>/api/v1/study</a> – start a spaced‑repetition session
            </div>
            <div class='endpoint'>
                <span class='method'>POST</span> <a href='/api/v1/study/{card_id}/review'>/api/v1/study/{card_id}/review</a> – submit review result
            </div>
        </div>
        <div class='card'>
            <h2>Tech Stack</h2>
            <ul>
                <li>FastAPI 0.115.0 (backend)</li>
                <li>PostgreSQL via SQLAlchemy 2.0.35</li>
                <li>DigitalOcean Serverless Inference (OpenAI‑compatible LLM)</li>
                <li>Python 3.12</li>
            </ul>
        </div>
        <p>Documentation: <a href='/docs'>/docs</a> | <a href='/redoc'>/redoc</a></p>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)
