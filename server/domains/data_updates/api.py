from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods

from server.application.web_support import data_update_repository, login_required_page, page_context


@require_http_methods(["GET", "POST"])
def data_updates_api(request):
    if request.method == "GET":
        return JsonResponse(data_update_repository.list_data_updates(), safe=False)
    return JsonResponse(data_update_repository.create_data_update(dict(request.POST)), status=201)

