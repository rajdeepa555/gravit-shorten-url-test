"""
FastAPI URL Shortener Application
"""
import sys
import time
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from common.utils import short_code, is_valid_url
from fastapi_app.models import ShortenUrl, get_db

app = FastAPI(title="URL Shortener API")


@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    """Home page with API documentation and shortened URLs."""
    base = str(request.base_url).rstrip('/')
    urls = db.query(ShortenUrl).order_by(ShortenUrl.created_at.desc()).all()
    url_rows = ''.join(
        f'<tr><td>{u.short_code}</td><td><a href="{u.original_url}" target="_blank">{u.original_url[:60]}{"..." if len(u.original_url) > 60 else ""}</a></td><td><a href="{base}/{u.short_code}">{base}/{u.short_code}</a></td></tr>'
        for u in urls
    ) or '<tr><td colspan="3">No shortened URLs yet.</td></tr>'
    return f'''<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>URL Shortener - FastAPI</title>
<style>body{{font-family:system-ui,sans-serif;max-width:800px;margin:2rem auto;padding:0 1rem}}h1{{color:#333}}code{{background:#f4f4f4;padding:2px 6px;border-radius:4px}}table{{width:100%;border-collapse:collapse}}th,td{{padding:8px;text-align:left;border-bottom:1px solid #ddd}}th{{background:#f8f8f8}}</style>
</head>
<body>
<h1>🔗 URL Shortener API</h1>
<p><strong>Framework:</strong> FastAPI</p>
<p>Shorten long URLs and redirect using compact short codes. Built with FastAPI, SQLAlchemy, and SQLite.</p>

<h2>Available API Endpoints</h2>
<table>
<tr><th>Method</th><th>Endpoint</th><th>Description</th></tr>
<tr><td><code>GET</code></td><td><a href="{base}/api/urls">{base}/api/urls</a></td><td>Get all shortened URLs (JSON)</td></tr>
<tr><td><code>POST</code></td><td><a href="{base}/api/shorten">{base}/api/shorten</a></td><td>Shorten a URL (body: {"{ \"url\": \"https://example.com\" }"})</td></tr>
<tr><td><code>GET</code></td><td><code>{base}/&#123;short_code&#125;</code></td><td>Redirect to original URL</td></tr>
</table>

<h2>Shortened URLs</h2>
<table><tr><th>Short Code</th><th>Original URL</th><th>Short Link</th></tr>{url_rows}</table>
</body>
</html>'''


class ShortenRequest(BaseModel):
    url: str


@app.get("/api/urls")
def get_all_urls(db: Session = Depends(get_db)):
    """Get all created shortened URLs."""
    urls = db.query(ShortenUrl).order_by(ShortenUrl.created_at.desc()).all()
    return [url.to_dict() for url in urls]


@app.post("/api/shorten", status_code=201)
def shorten_url(data: ShortenRequest, db: Session = Depends(get_db)):
    """Shorten a URL and save to database. Returns 201 on success, 400 on error."""
    url = data.url.strip() if data.url else ""
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    if not is_valid_url(url):
        raise HTTPException(status_code=400, detail="Invalid or unavailable URL")

    existing = db.query(ShortenUrl).filter(ShortenUrl.original_url == url).first()
    if existing:
        return existing.to_dict()

    code = short_code(url)
    while db.query(ShortenUrl).filter(ShortenUrl.short_code == code).first():
        code = short_code(url + str(time.time()))[:8]

    record = ShortenUrl(original_url=url, short_code=code)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record.to_dict()


@app.get("/{code}")
def redirect_to_original(code: str, db: Session = Depends(get_db)):
    """Redirect short code to original URL."""
    record = db.query(ShortenUrl).filter(ShortenUrl.short_code == code).first()
    if not record:
        raise HTTPException(status_code=404, detail="Short URL not found")
    return RedirectResponse(url=record.original_url, status_code=302)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
