from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from server.core.dependencies import repository


@require_http_methods(["POST"])
def signup_api(request):
    username = request.POST.get("username", "").strip()
    display_name = request.POST.get("display_name", "").strip()
    email = request.POST.get("email", "").strip()
    password = request.POST.get("password", "").strip()
    role = request.POST.get("role", "member").strip()
    if not all([username, display_name, email, password]):
        return JsonResponse({"detail": "username/display_name/email/password는 필수입니다."}, status=400)

    try:
        registered = repository.register_user(
            username=username,
            display_name=display_name,
            email=email,
            password=password,
            role=role,
            team_name=request.POST.get("team_name", "").strip(),
            team_description=request.POST.get("team_description", "").strip(),
            team_code=request.POST.get("team_code", "").strip(),
        )
    except ValueError as exc:
        return JsonResponse({"detail": str(exc)}, status=400)

    return JsonResponse(registered, status=201)
