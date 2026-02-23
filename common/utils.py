"""
Shared utility functions for URL shortening across all framework versions.
"""
import hashlib
import re
from urllib.parse import urlparse


def short_code(url: str) -> str:
    """
    Generate a short code for the given URL.
    Uses MD5 hash and takes first 8 characters for uniqueness.
    """
    hash_value = hashlib.md5(url.encode()).hexdigest()
    return hash_value[:8]


def is_valid_url(url: str) -> bool:
    """
    Validate if the given string is a valid URL.
    """
    if not url or not isinstance(url, str):
        return False
    
    url = url.strip()
    if not url:
        return False
    
    # Basic URL pattern
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )
    
    try:
        result = urlparse(url)
        return all([result.scheme in ('http', 'https'), result.netloc, url_pattern.match(url)])
    except Exception:
        return False
