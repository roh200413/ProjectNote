from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from projectnote.server.core.dependencies import repository


@require_http_methods(["GET", "POST"])
def data_updates_api(request):
    if request.method == "GET":
        return JsonResponse(repository.list_data_updates(), safe=False)
    return JsonResponse(repository.create_data_update(request.POST), status=201)
