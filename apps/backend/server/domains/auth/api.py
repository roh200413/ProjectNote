from datetime import datetime, timezone

from django.contrib.auth import get_user_model, login, logout
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods


User = get_user_model()

from server.application.web_support import (
    authenticate_login_user,
    authenticate_super_admin,
    admin_repository,
    effective_user_profile,
    save_login_session,
)


def _resolve_login_user(username: str, password: str) -> dict | None:
    user = authenticate_login_user(username, password)
    if not user:
        super_admin_user = authenticate_super_admin(username, password)
        if super_admin_user:
            user = {**super_admin_user, "is_super_admin": True}
    return user


@require_GET
def health(_request):
    return JsonResponse({"status": "ok"})




def _sync_and_login_django_user(request, username: str, password: str, email: str, is_super_admin: bool = False) -> None:
    django_user, created = User.objects.get_or_create(
        username=username,
        defaults={"email": email or f"{username}@projectnote.local"},
    )
    should_save = False
    if created:
        django_user.set_password(password)
        should_save = True
    elif password and not django_user.check_password(password):
        django_user.set_password(password)
        should_save = True

    if django_user.is_staff != bool(is_super_admin):
        django_user.is_staff = bool(is_super_admin)
        should_save = True
    if django_user.is_superuser != bool(is_super_admin):
        django_user.is_superuser = bool(is_super_admin)
        should_save = True

    if should_save:
        django_user.save()

    login(request, django_user, backend="django.contrib.auth.backends.ModelBackend")

@require_http_methods(["GET", "POST"])
@ensure_csrf_cookie
def login_page(request):
    if request.method == "GET":
        user_profile = effective_user_profile(request)
        if user_profile:
            if user_profile.get("is_super_admin"):
                return redirect("/frontend/admin/dashboard")
            return redirect("/frontend/workflows")
        return render(request, "auth/login.html", {"error": "", "next": request.GET.get("next", "")})

    username = request.POST.get("username", "").strip()
    password = request.POST.get("password", "")
    next_url = request.POST.get("next", "")
    user = _resolve_login_user(username, password)
    if not user:
        return render(
            request,
            "auth/login.html",
            {"error": "아이디 또는 비밀번호가 올바르지 않습니다.", "next": next_url},
            status=401,
        )

    if not user.get("is_super_admin") and user.get("team") in {None, "-", ""}:
        if bool(user.get("requested_team_name")) and not bool(user.get("is_approved", False)):
            return render(
                request,
                "auth/login.html",
                {"error": "관리자 승인 대기 중입니다.", "next": next_url},
                status=403,
            )
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
    _sync_and_login_django_user(request, username, password, user.get("email", ""), bool(user.get("is_super_admin", False)))
    if next_url.startswith("/"):
        return redirect(next_url)
    if user.get("is_super_admin"):
        return redirect("/frontend/admin/dashboard")
    return redirect("/frontend/workflows")


@csrf_exempt
@require_http_methods(["POST"])
@ensure_csrf_cookie
def login_api(request):
    username = request.POST.get("username", "").strip()
    password = request.POST.get("password", "")
    user = _resolve_login_user(username, password)
    if not user:
        return JsonResponse({"detail": "아이디 또는 비밀번호가 올바르지 않습니다."}, status=401)

    if not user.get("is_super_admin") and user.get("team") in {None, "-", ""}:
        if bool(user.get("requested_team_name")) and not bool(user.get("is_approved", False)):
            return JsonResponse({"detail": "관리자 승인 대기 중입니다."}, status=403)
        return JsonResponse({"detail": "관리자 팀 할당 및 승인이 되지 않았습니다."}, status=403)

    if not user.get("is_super_admin") and not bool(user.get("is_approved", False)):
        return JsonResponse({"detail": "관리자 승인 대기 중입니다."}, status=403)

    save_login_session(request, username, user)
    _sync_and_login_django_user(request, username, password, user.get("email", ""), bool(user.get("is_super_admin", False)))
    return JsonResponse({"message": "로그인 성공", "user": user})


@require_http_methods(["GET", "POST"])
@ensure_csrf_cookie
def admin_login_page(request):
    if request.method == "GET":
        if (effective_user_profile(request) or {}).get("is_super_admin") or request.user.is_staff or request.user.is_superuser:
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
    _sync_and_login_django_user(request, username, password, user.get("email", ""), bool(user.get("is_super_admin", False)))
    if next_url.startswith("/frontend/admin"):
        return redirect(next_url)
    return redirect("/frontend/admin/dashboard")


@require_GET
@ensure_csrf_cookie
def signup_page(request):
    if effective_user_profile(request):
        return redirect("/frontend/workflows")
    return render(request, "auth/signup.html", {"next": request.GET.get("next", "")})


@require_GET
def logout_page(request):
    logout(request)
    request.session.pop("user_profile", None)
    return redirect("/login")


@csrf_exempt
@require_http_methods(["POST"])
def logout_api(request):
    logout(request)
    request.session.pop("user_profile", None)
    return JsonResponse({"message": "로그아웃되었습니다."})


@require_GET
def me_api(request):
    profile = effective_user_profile(request)
    if not profile:
        return JsonResponse({"detail": "인증이 필요합니다."}, status=401)
    return JsonResponse({"user": profile})


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
