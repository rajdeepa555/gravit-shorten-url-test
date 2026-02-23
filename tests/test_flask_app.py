"""
Tests for Flask URL shortener.
"""
import os
import sys
import json
import tempfile

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from flask_app.app import app
from flask_app.models import db, ShortenUrl


@pytest.fixture
def client():
    """Create test client with temporary database."""
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()


def test_get_all_urls_empty(client):
    """Test get_all_urls returns empty list when no URLs exist."""
    response = client.get('/api/urls')
    assert response.status_code == 200
    assert json.loads(response.data) == []


def test_shorten_url_success(client):
    """Test shorten_url creates URL and returns 201."""
    response = client.post('/api/shorten', data=json.dumps({'url': 'https://example.com'}), 
                          content_type='application/json')
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['original_url'] == 'https://example.com'
    assert 'short_code' in data
    assert len(data['short_code']) == 8
    assert 'id' in data
    assert 'created_at' in data


def test_shorten_url_invalid_missing_url(client):
    """Test shorten_url returns 400 when URL is missing."""
    response = client.post('/api/shorten', data=json.dumps({}), content_type='application/json')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'message' in data
    assert 'URL' in data['message']


def test_shorten_url_invalid_empty_body(client):
    """Test shorten_url returns 400 when body is empty."""
    response = client.post('/api/shorten', data=None, content_type='application/json')
    assert response.status_code == 400


def test_shorten_url_invalid_url(client):
    """Test shorten_url returns 400 for invalid URL."""
    response = client.post('/api/shorten', data=json.dumps({'url': 'not-a-valid-url'}), 
                          content_type='application/json')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'message' in data
    assert 'Invalid' in data['message']


def test_shorten_url_invalid_empty_string(client):
    """Test shorten_url returns 400 for empty URL."""
    response = client.post('/api/shorten', data=json.dumps({'url': '   '}), 
                          content_type='application/json')
    assert response.status_code == 400


def test_get_all_urls_after_shorten(client):
    """Test get_all_urls returns created URLs."""
    client.post('/api/shorten', data=json.dumps({'url': 'https://google.com'}), 
                content_type='application/json')
    response = client.get('/api/urls')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 1
    assert data[0]['original_url'] == 'https://google.com'


def test_redirect_to_original(client):
    """Test redirect takes short_code to original URL."""
    shorten_resp = client.post('/api/shorten', data=json.dumps({'url': 'https://python.org'}), 
                               content_type='application/json')
    short_code = json.loads(shorten_resp.data)['short_code']
    response = client.get(f'/{short_code}', follow_redirects=False)
    assert response.status_code == 302
    assert response.location == 'https://python.org'


def test_redirect_not_found(client):
    """Test redirect returns 404 for non-existent short code."""
    response = client.get('/nonexistent')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'message' in data
    assert 'not found' in data['message'].lower()


def test_shorten_same_url_twice(client):
    """Test shortening same URL returns existing record with 201."""
    url = 'https://github.com'
    r1 = client.post('/api/shorten', data=json.dumps({'url': url}), content_type='application/json')
    r2 = client.post('/api/shorten', data=json.dumps({'url': url}), content_type='application/json')
    assert r1.status_code == 201
    assert r2.status_code == 201
    d1, d2 = json.loads(r1.data), json.loads(r2.data)
    assert d1['short_code'] == d2['short_code']
    assert d1['original_url'] == d2['original_url']
