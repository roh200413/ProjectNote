from datetime import datetime, timezone

from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods

from server.application.web_support import (
    authenticate_login_user,
    authenticate_super_admin,
    admin_repository,
    save_login_session,
)


@require_GET
def health(_request):
    return JsonResponse({"status": "ok"})


@require_http_methods(["GET", "POST"])
@ensure_csrf_cookie
def login_page(request):
    if request.method == "GET":
        user_profile = request.session.get("user_profile")
        if user_profile:
            if user_profile.get("is_super_admin"):
                return redirect("/frontend/admin/dashboard")
            return redirect("/frontend/workflows")
        return render(request, "auth/login.html", {"error": "", "next": request.GET.get("next", "")})

    username = request.POST.get("username", "").strip()
    password = request.POST.get("password", "")
    next_url = request.POST.get("next", "")
    user = authenticate_login_user(username, password)
    if not user:
        super_admin_user = authenticate_super_admin(username, password)
        if super_admin_user:
            user = {**super_admin_user, "is_super_admin": True}
    if not user:
        return render(
            request,
            "auth/login.html",
            {"error": "아이디 또는 비밀번호가 올바르지 않습니다.", "next": next_url},
            status=401,
        )

    if not user.get("is_super_admin") and user.get("team") in {None, "-", ""}:
        return render(
            request,
            "auth/login.html",
            {"error": "관리자 팀 할당 및 승인이 되지 않았습니다.", "next": next_url},
            status=403,
        )
    if not user.get("is_super_admin") and not bool(user.get("is_approved", False)):
        return render(
            request,
            "auth/login.html",
            {"error": "관리자 승인 대기 중입니다.", "next": next_url},
            status=403,
        )

    save_login_session(request, username, user)
    if next_url.startswith("/"):
        return redirect(next_url)
    if user.get("is_super_admin"):
        return redirect("/frontend/admin/dashboard")
    return redirect("/frontend/workflows")


@require_http_methods(["GET", "POST"])
@ensure_csrf_cookie
def admin_login_page(request):
    if request.method == "GET":
        if request.session.get("user_profile", {}).get("is_super_admin"):
            return redirect("/frontend/admin/dashboard")
        return render(request, "auth/admin_login.html", {"error": "", "next": request.GET.get("next", "")})

    username = request.POST.get("username", "").strip()
    password = request.POST.get("password", "")
    next_url = request.POST.get("next", "")
    user = authenticate_super_admin(username, password)
    if not user:
        return render(
            request,
            "auth/admin_login.html",
            {"error": "슈퍼 어드민 계정으로만 로그인할 수 있습니다.", "next": next_url},
            status=401,
        )

    save_login_session(request, username, user)
    if next_url.startswith("/frontend/admin"):
        return redirect(next_url)
    return redirect("/frontend/admin/dashboard")


@require_GET
@ensure_csrf_cookie
def signup_page(request):
    if request.session.get("user_profile"):
        return redirect("/frontend/workflows")
    return render(request, "auth/signup.html", {"next": request.GET.get("next", "")})


@require_GET
def logout_page(request):
    request.session.pop("user_profile", None)
    return redirect("/login")


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
        registered = admin_repository.register_user(
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


@require_GET
def frontend_bootstrap(_request):
    return JsonResponse(
        {
            "api_name": "ProjectNote API",
            "api_version": "v1",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
