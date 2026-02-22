from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_http_methods

from server.core.dependencies import repository, service
from server.core.http import parse_uuid_or_422


@require_GET
def projects(request):
    maybe_error = parse_uuid_or_422("org_id", request.GET.get("org_id"))
    if maybe_error is not None and not hasattr(maybe_error, "hex"):
        return maybe_error
    return JsonResponse(repository.list_projects(), safe=False)


@require_http_methods(["GET", "POST"])
def project_management_api(request):
    if request.method == "GET":
        return JsonResponse(repository.list_projects(), safe=False)
    project = service.create_project(request.POST)
    return JsonResponse(project, status=201)
