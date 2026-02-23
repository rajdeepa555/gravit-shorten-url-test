"""
SQLAlchemy models for Flask URL shortener.
"""
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class ShortenUrl(db.Model):
    """Model for storing shortened URL details."""
    __tablename__ = 'shorten_url'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    original_url = db.Column(db.String(2048), nullable=False)
    short_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'original_url': self.original_url,
            'short_code': self.short_code,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
