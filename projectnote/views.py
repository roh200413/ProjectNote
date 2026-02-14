import uuid
from datetime import datetime, timezone

from django.http import JsonResponse
from django.views.decorators.http import require_GET


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
    return JsonResponse({"organizations": 0, "projects": 0, "notes": 0, "revisions": 0})


@require_GET
def projects(request):
    org_id = request.GET.get("org_id")

    if org_id:
        try:
            uuid.UUID(org_id)
        except ValueError:
            return JsonResponse(
                {
                    "detail": [
                        {
                            "type": "uuid_parsing",
                            "loc": ["query", "org_id"],
                            "msg": "Input should be a valid UUID.",
                            "input": org_id,
                        }
                    ]
                },
                status=422,
            )

    return JsonResponse([], safe=False)
