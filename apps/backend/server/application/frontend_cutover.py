from __future__ import annotations

from django.conf import settings
from django.http import HttpResponseRedirect


def frontend_cutover_redirect(request, legacy_path: str = ""):
    web_origin = str(getattr(settings, "WEB_APP_ORIGIN", "http://127.0.0.1:3000")).rstrip("/")
    destination = f"{web_origin}/frontend"
    if legacy_path:
        destination = f"{destination}/{legacy_path.lstrip('/')}"

    query_string = request.META.get("QUERY_STRING", "")
    if query_string:
        destination = f"{destination}?{query_string}"
    return HttpResponseRedirect(destination)
