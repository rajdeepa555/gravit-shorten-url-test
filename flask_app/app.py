"""
Flask URL Shortener Application
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, jsonify, request, redirect
from common.utils import short_code, is_valid_url
from flask_app.models import db, ShortenUrl

app = Flask(__name__)


def _get_base_url():
    return request.url_root.rstrip('/')


def _render_home_page():
    urls = ShortenUrl.query.order_by(ShortenUrl.created_at.desc()).all()
    base = _get_base_url()
    url_rows = ''.join(
        f'<tr><td>{u.short_code}</td><td><a href="{u.original_url}" target="_blank">{u.original_url[:60]}{"..." if len(u.original_url) > 60 else ""}</a></td><td><a href="{base}/{u.short_code}">{base}/{u.short_code}</a></td></tr>'
        for u in urls
    ) or '<tr><td colspan="3">No shortened URLs yet.</td></tr>'
    return f'''<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>URL Shortener - Flask</title>
<style>body{{font-family:system-ui,sans-serif;max-width:800px;margin:2rem auto;padding:0 1rem}}h1{{color:#333}}code{{background:#f4f4f4;padding:2px 6px;border-radius:4px}}table{{width:100%;border-collapse:collapse}}th,td{{padding:8px;text-align:left;border-bottom:1px solid #ddd}}th{{background:#f8f8f8}}</style>
</head>
<body>
<h1>🔗 URL Shortener API</h1>
<p><strong>Framework:</strong> Flask</p>
<p>Shorten long URLs and redirect using compact short codes. Built with Flask, SQLAlchemy, and SQLite.</p>

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
_db_path = os.path.join(os.path.dirname(__file__), 'shorten_url.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{_db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


@app.route('/')
def home():
    """Home page with API documentation and shortened URLs."""
    return _render_home_page()


@app.before_request
def _ensure_tables():
    """Ensure database tables exist."""
    pass  # Tables created in main block


@app.route('/api/urls', methods=['GET'])
def get_all_urls():
    """Get all created shortened URLs."""
    urls = ShortenUrl.query.order_by(ShortenUrl.created_at.desc()).all()
    return jsonify([url.to_dict() for url in urls])


@app.route('/api/shorten', methods=['POST'])
def shorten_url():
    """Shorten a URL and save to database. Returns 201 on success, 400 on error."""
    data = request.get_json()
    if data is None or not isinstance(data, dict):
        return jsonify({'message': 'Request body is required'}), 400

    url = data.get('url')
    if not url:
        return jsonify({'message': 'URL is required'}), 400

    url = url.strip()
    if not is_valid_url(url):
        return jsonify({'message': 'Invalid or unavailable URL'}), 400

    code = short_code(url)
    existing = ShortenUrl.query.filter_by(original_url=url).first()
    if existing:
        return jsonify(existing.to_dict()), 201

    existing_code = ShortenUrl.query.filter_by(short_code=code).first()
    if existing_code:
        import time
        code = short_code(url + str(time.time()))[:8]

    shorten_url_record = ShortenUrl(original_url=url, short_code=code)
    db.session.add(shorten_url_record)
    db.session.commit()

    return jsonify(shorten_url_record.to_dict()), 201


@app.route('/<code>', methods=['GET'])
def redirect_to_original(code):
    """Redirect short code to original URL."""
    record = ShortenUrl.query.filter_by(short_code=code).first()
    if not record:
        return jsonify({'message': 'Short URL not found'}), 404
    return redirect(record.original_url, code=302)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=8002)
