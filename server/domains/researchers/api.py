from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods

from server.application.web_support import login_required_page, page_context, researcher_repository


@require_http_methods(["GET", "POST"])
def researchers_api(request):
    if request.method == "GET":
        return JsonResponse(researcher_repository.list_researchers(), safe=False)
    return JsonResponse(researcher_repository.create_researcher(dict(request.POST)), status=201)


@require_GET
@ensure_csrf_cookie
@login_required_page
def researchers_page(request):
    return render(request, "workflow/researchers.html", page_context(request, {"researchers": researcher_repository.list_researchers()}))
