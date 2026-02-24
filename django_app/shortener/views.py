"""
Views for Django URL shortener.
"""
import time
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from common.utils import short_code, is_valid_url
from shortener.models import ShortenUrl


@require_http_methods(["GET"])
def home(request):
    """Home page with API documentation and shortened URLs."""
    base = request.build_absolute_uri('/').rstrip('/')
    urls = ShortenUrl.objects.all().order_by('-created_at')
    url_rows = ''.join(
        f'<tr><td>{u.short_code}</td><td><a href="{u.original_url}" target="_blank">{u.original_url[:60]}{"..." if len(u.original_url) > 60 else ""}</a></td><td><a href="{base}/{u.short_code}">{base}/{u.short_code}</a></td></tr>'
        for u in urls
    ) or '<tr><td colspan="3">No shortened URLs yet.</td></tr>'
    html = f'''<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>URL Shortener - Django</title>
<style>body{{font-family:system-ui,sans-serif;max-width:800px;margin:2rem auto;padding:0 1rem}}h1{{color:#333}}code{{background:#f4f4f4;padding:2px 6px;border-radius:4px}}table{{width:100%;border-collapse:collapse}}th,td{{padding:8px;text-align:left;border-bottom:1px solid #ddd}}th{{background:#f8f8f8}}</style>
</head>
<body>
<h1>🔗 URL Shortener API</h1>
<p><strong>Framework:</strong> Django</p>
<p>Shorten long URLs and redirect using compact short codes. Built with Django, Django ORM, and SQLite.</p>

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
    return HttpResponse(html)


@require_http_methods(["GET"])
def get_all_urls(request):
    """Get all created shortened URLs."""
    urls = ShortenUrl.objects.all().order_by('-created_at')
    return JsonResponse([url.to_dict() for url in urls], safe=False)


@csrf_exempt
@require_http_methods(["POST"])
def shorten_url(request):
    """Shorten a URL and save to database. Returns 201 on success, 400 on error."""
    import json
    try:
        data = json.loads(request.body.decode()) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({'message': 'Invalid JSON'}, status=400)

    url = data.get('url')
    if not url:
        return JsonResponse({'message': 'URL is required'}, status=400)

    url = str(url).strip()
    if not is_valid_url(url):
        return JsonResponse({'message': 'Invalid or unavailable URL'}, status=400)

    existing = ShortenUrl.objects.filter(original_url=url).first()
    if existing:
        return JsonResponse(existing.to_dict(), status=201)

    code = short_code(url)
    while ShortenUrl.objects.filter(short_code=code).exists():
        code = short_code(url + str(time.time()))[:8]

    record = ShortenUrl.objects.create(original_url=url, short_code=code)
    return JsonResponse(record.to_dict(), status=201)


@require_http_methods(["GET"])
def redirect_to_original(request, code):
    """Redirect short code to original URL."""
    try:
        record = ShortenUrl.objects.get(short_code=code)
    except ShortenUrl.DoesNotExist:
        return JsonResponse({'message': 'Short URL not found'}, status=404)
    return HttpResponseRedirect(record.original_url, status=302)
