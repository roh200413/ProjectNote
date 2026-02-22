from datetime import datetime, timezone

from django.http import JsonResponse
from django.views.decorators.http import require_GET

from server.core.dependencies import repository


@require_GET
def health(_request):
    return JsonResponse({"status": "ok"})


@require_GET
def frontend_bootstrap(_request):
    return JsonResponse(
        {
            "api_name": "ProjectNote API",
            "api_version": "v1",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


@require_GET
def dashboard_summary(_request):
    return JsonResponse(repository.dashboard_counts())


@require_GET
def final_download_api(_request):
    payload = {
        "format": "pdf",
        "status": "ready",
        "download_url": "/downloads/projectnote-final-report.pdf",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    return JsonResponse(payload)
