from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from server.core.dependencies import repository


@require_http_methods(["GET", "POST"])
def signature_api(request):
    if request.method == "GET":
        return JsonResponse(repository.read_signature())
    payload = repository.update_signature(
        signed_by=request.POST.get("signed_by", ""), status=request.POST.get("status", "valid")
    )
    return JsonResponse(payload)
