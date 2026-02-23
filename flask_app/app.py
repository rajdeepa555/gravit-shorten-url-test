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
_db_path = os.path.join(os.path.dirname(__file__), 'shorten_url.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{_db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


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
