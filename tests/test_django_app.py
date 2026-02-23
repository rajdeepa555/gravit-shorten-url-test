"""
Tests for Django URL shortener.
"""
import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'django_app')))

import pytest
from django.test import TestCase, Client
from django.urls import reverse

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_app.settings')
import django
django.setup()


class URLShortenerTests(TestCase):
    """Test cases for Django URL shortener APIs."""

    def setUp(self):
        self.client = Client()

    def test_get_all_urls_empty(self):
        """Test get_all_urls returns empty list when no URLs exist."""
        response = self.client.get('/api/urls')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), [])

    def test_shorten_url_success(self):
        """Test shorten_url creates URL and returns 201."""
        response = self.client.post(
            '/api/shorten',
            data=json.dumps({'url': 'https://example.com'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertEqual(data['original_url'], 'https://example.com')
        self.assertIn('short_code', data)
        self.assertEqual(len(data['short_code']), 8)
        self.assertIn('id', data)
        self.assertIn('created_at', data)

    def test_shorten_url_invalid_missing_url(self):
        """Test shorten_url returns 400 when URL is missing."""
        response = self.client.post(
            '/api/shorten',
            data=json.dumps({}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('message', data)
        self.assertIn('URL', data['message'])

    def test_shorten_url_invalid_url(self):
        """Test shorten_url returns 400 for invalid URL."""
        response = self.client.post(
            '/api/shorten',
            data=json.dumps({'url': 'not-a-valid-url'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('message', data)
        self.assertIn('Invalid', data['message'])

    def test_shorten_url_invalid_empty_string(self):
        """Test shorten_url returns 400 for empty URL."""
        response = self.client.post(
            '/api/shorten',
            data=json.dumps({'url': '   '}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_get_all_urls_after_shorten(self):
        """Test get_all_urls returns created URLs."""
        self.client.post(
            '/api/shorten',
            data=json.dumps({'url': 'https://google.com'}),
            content_type='application/json'
        )
        response = self.client.get('/api/urls')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['original_url'], 'https://google.com')

    def test_redirect_to_original(self):
        """Test redirect takes short_code to original URL."""
        shorten_resp = self.client.post(
            '/api/shorten',
            data=json.dumps({'url': 'https://python.org'}),
            content_type='application/json'
        )
        short_code = json.loads(shorten_resp.content)['short_code']
        response = self.client.get(f'/{short_code}')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, 'https://python.org')

    def test_redirect_not_found(self):
        """Test redirect returns 404 for non-existent short code."""
        response = self.client.get('/nonexistent')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertIn('message', data)
        self.assertIn('not found', data['message'].lower())

    def test_shorten_same_url_twice(self):
        """Test shortening same URL returns existing record with 201."""
        url = 'https://github.com'
        r1 = self.client.post(
            '/api/shorten',
            data=json.dumps({'url': url}),
            content_type='application/json'
        )
        r2 = self.client.post(
            '/api/shorten',
            data=json.dumps({'url': url}),
            content_type='application/json'
        )
        self.assertEqual(r1.status_code, 201)
        self.assertEqual(r2.status_code, 201)
        d1, d2 = json.loads(r1.content), json.loads(r2.content)
        self.assertEqual(d1['short_code'], d2['short_code'])
        self.assertEqual(d1['original_url'], d2['original_url'])
