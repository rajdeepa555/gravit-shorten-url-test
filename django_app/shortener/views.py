"""
Views for Django URL shortener.
"""
import time
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.clickjacking import xframe_options_exempt

from common.utils import short_code, is_valid_url
from shortener.models import ShortenUrl


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
