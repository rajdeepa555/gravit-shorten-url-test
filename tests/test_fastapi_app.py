"""
Tests for FastAPI URL shortener.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from fastapi.testclient import TestClient

# Import after path setup
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi_app.models import Base, get_db

# Use temp file for test DB - in-memory has connection isolation issues
_test_db_path = os.path.join(os.path.dirname(__file__), 'fastapi_test.db')
TEST_DATABASE_URL = f"sqlite:///{_test_db_path}"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    """Create test client with temporary database."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    from fastapi_app.app import app
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_get_all_urls_empty(client):
    """Test get_all_urls returns empty list when no URLs exist."""
    response = client.get("/api/urls")
    assert response.status_code == 200
    assert response.json() == []


def test_shorten_url_success(client):
    """Test shorten_url creates URL and returns 201."""
    response = client.post("/api/shorten", json={"url": "https://example.com"})
    assert response.status_code == 201
    data = response.json()
    assert data["original_url"] == "https://example.com"
    assert "short_code" in data
    assert len(data["short_code"]) == 8
    assert "id" in data
    assert "created_at" in data


def test_shorten_url_invalid_missing_url(client):
    """Test shorten_url returns 400 when URL is missing or empty."""
    response = client.post("/api/shorten", json={"url": ""})
    assert response.status_code in (400, 422)  # 400 from our validation, 422 from Pydantic


def test_shorten_url_invalid_url(client):
    """Test shorten_url returns 400 for invalid URL."""
    response = client.post("/api/shorten", json={"url": "not-a-valid-url"})
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Invalid" in data["detail"]


def test_shorten_url_invalid_empty_string(client):
    """Test shorten_url returns 400 for empty URL."""
    response = client.post("/api/shorten", json={"url": "   "})
    assert response.status_code == 400


def test_get_all_urls_after_shorten(client):
    """Test get_all_urls returns created URLs."""
    client.post("/api/shorten", json={"url": "https://google.com"})
    response = client.get("/api/urls")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["original_url"] == "https://google.com"


def test_redirect_to_original(client):
    """Test redirect takes short_code to original URL."""
    shorten_resp = client.post("/api/shorten", json={"url": "https://python.org"})
    short_code = shorten_resp.json()["short_code"]
    response = client.get(f"/{short_code}", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "https://python.org"


def test_redirect_not_found(client):
    """Test redirect returns 404 for non-existent short code."""
    response = client.get("/nonexistent")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


def test_shorten_same_url_twice(client):
    """Test shortening same URL returns existing record with 201."""
    url = "https://github.com"
    r1 = client.post("/api/shorten", json={"url": url})
    r2 = client.post("/api/shorten", json={"url": url})
    assert r1.status_code == 201
    assert r2.status_code == 201
    d1, d2 = r1.json(), r2.json()
    assert d1["short_code"] == d2["short_code"]
    assert d1["original_url"] == d2["original_url"]
