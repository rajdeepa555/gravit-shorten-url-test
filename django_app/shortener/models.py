"""
Models for Django URL shortener.
"""
from django.db import models


class ShortenUrl(models.Model):
    """Model for storing shortened URL details."""
    original_url = models.CharField(max_length=2048)
    short_code = models.CharField(max_length=50, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'shorten_url'

    def to_dict(self):
        return {
            'id': self.id,
            'original_url': self.original_url,
            'short_code': self.short_code,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
