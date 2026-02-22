from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from projectnote.server.core.dependencies import repository


@require_http_methods(["GET", "POST"])
def researchers_api(request):
    if request.method == "GET":
        return JsonResponse(repository.list_researchers(), safe=False)
    return JsonResponse(repository.create_researcher(request.POST), status=201)
