from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods

from server.application.web_support import effective_user_profile, login_required_page, page_context, researcher_repository
from server.domains.admin.models import Team


def _can_manage(request) -> bool:
    profile = effective_user_profile(request) or {}
    role = profile.get("role")
    return bool(
        request.user.is_staff
        or request.user.is_superuser
        or profile.get("is_super_admin")
        or role in {"소유자", "owner", "관리자", "admin"}
    )


def _resolve_team_id_from_session(profile: dict) -> int | None:
    team_id = profile.get("team_id")
    if team_id:
        try:
            return int(team_id)
        except (TypeError, ValueError):
            pass

    team_name = str(profile.get("team", "")).strip()
    organization_name = str(profile.get("organization", "")).strip()
    for candidate in (team_name, organization_name):
        if not candidate or candidate in {"-", "미지정"}:
            continue
        team = Team.objects.filter(name=candidate).first()
        if team:
            return team.id
    return None


def _can_manage(request) -> bool:
    profile = request.session.get("user_profile", {})
    return bool(profile.get("is_super_admin") or profile.get("role") == "관리자")


@require_http_methods(["GET", "POST"])
@login_required_page
def researchers_api(request):
    profile = effective_user_profile(request) or {}
    team_id = _resolve_team_id_from_session(profile)

    if request.method == "GET":
        return JsonResponse(researcher_repository.list_researchers(), safe=False)

    action = request.POST.get("action", "create").strip()
    if action == "create":
        try:
            created = researcher_repository.create_researcher(dict(request.POST))
        except ValueError as exc:
            return JsonResponse({"detail": str(exc)}, status=400)
        return JsonResponse(created, status=201)

    if not _can_manage(request):
        return JsonResponse({"detail": "관리 권한이 없습니다."}, status=403)

    user_id_raw = request.POST.get("user_id", "").strip()
    if not user_id_raw.isdigit():
        return JsonResponse({"detail": "유효한 사용자 ID가 필요합니다."}, status=400)
    user_id = int(user_id_raw)

    try:
        if action == "approve":
            payload = researcher_repository.approve_user(user_id)
        elif action == "grant_role":
            payload = researcher_repository.grant_role(user_id, request.POST.get("role", "").strip())
        elif action == "assign_team":
            team_id_raw = request.POST.get("team_id", "").strip()
            team_id = int(team_id_raw) if team_id_raw.isdigit() else None
            payload = researcher_repository.assign_team(user_id, team_id)
        elif action == "expel":
            payload = researcher_repository.expel_user(user_id)
        else:
            return JsonResponse({"detail": "지원하지 않는 작업입니다."}, status=400)
    except ValueError as exc:
        return JsonResponse({"detail": str(exc)}, status=400)
    return JsonResponse(payload)


@require_GET
@ensure_csrf_cookie
@login_required_page
def researchers_page(request):
    return render(
        request,
        "workflow/researchers.html",
        page_context(
            request,
            {
                "researchers": researcher_repository.list_researchers(),
                "teams": researcher_repository.list_teams(),
                "can_manage_researchers": _can_manage(request),
            },
        ),
    )

@require_GET
@ensure_csrf_cookie
@login_required_page
def github_integrations_page(request):
    return render(
        request,
        "workflow/github_integrations.html",
        page_context(request, {}),
    )


@require_GET
@ensure_csrf_cookie
@login_required_page
def collaboration_integrations_page(request):
    return render(
        request,
        "workflow/collaboration_integrations.html",
        page_context(request, {}),
    )

