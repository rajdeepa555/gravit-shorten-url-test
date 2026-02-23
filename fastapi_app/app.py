"""
FastAPI URL Shortener Application
"""
import sys
import time
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from common.utils import short_code, is_valid_url
from fastapi_app.models import ShortenUrl, get_db

app = FastAPI(title="URL Shortener API")


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
