from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods

from server.application.web_support import login_required_page, page_context, researcher_repository
from server.domains.admin.models import Team


def _can_manage(request) -> bool:
    profile = request.session.get("user_profile", {})
    return bool(profile.get("is_super_admin") or profile.get("role") == "관리자")


def _resolve_team_id_from_session(profile: dict) -> int | None:
    team_id = profile.get("team_id")
    if team_id:
        return int(team_id)
    team_name = str(profile.get("team", "")).strip()
    if not team_name or team_name == "-":
        return None
    team = Team.objects.filter(name=team_name).first()
    return team.id if team else None


@require_http_methods(["GET", "POST"])
@login_required_page
def researchers_api(request):
    profile = request.session.get("user_profile", {})
    team_id = _resolve_team_id_from_session(profile)

    if request.method == "GET":
        action = request.GET.get("action", "").strip()
        if action == "unassigned":
            query = request.GET.get("q", "").strip()
            return JsonResponse(researcher_repository.list_unassigned_users(query), safe=False)
        if action == "pending_by_code":
            join_code = request.GET.get("join_code", "").strip()
            return JsonResponse(researcher_repository.list_pending_users_by_join_code(join_code), safe=False)
        return JsonResponse(researcher_repository.list_researchers_for_team(team_id=team_id, approved_only=True), safe=False)

    action = request.POST.get("action", "create").strip()
    if action == "create":
        try:
            created = researcher_repository.create_researcher(dict(request.POST))
        except ValueError as exc:
            return JsonResponse({"detail": str(exc)}, status=400)
        return JsonResponse(created, status=201)

    if not _can_manage(request):
        return JsonResponse({"detail": "관리 권한이 없습니다."}, status=403)

    try:
        if action == "verify_id":
            payload = researcher_repository.verify_unassigned_user_id(request.POST.get("username", ""))
        elif action == "assign_team":
            username = request.POST.get("username", "").strip()
            if username:
                payload = researcher_repository.assign_team_by_username(username, team_id)
            else:
                user_id_raw = request.POST.get("user_id", "").strip()
                if not user_id_raw.isdigit():
                    return JsonResponse({"detail": "유효한 사용자 ID가 필요합니다."}, status=400)
                user_id = int(user_id_raw)
                team_id_raw = request.POST.get("team_id", "").strip()
                assign_team_id = int(team_id_raw) if team_id_raw.isdigit() else None
                payload = researcher_repository.assign_team(user_id, assign_team_id)
        else:
            user_id_raw = request.POST.get("user_id", "").strip()
            if not user_id_raw.isdigit():
                return JsonResponse({"detail": "유효한 사용자 ID가 필요합니다."}, status=400)
            user_id = int(user_id_raw)
            if action == "approve":
                payload = researcher_repository.approve_user(user_id)
            elif action == "grant_role":
                payload = researcher_repository.grant_role(user_id, request.POST.get("role", "").strip())
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
    profile = request.session.get("user_profile", {})
    team_id = _resolve_team_id_from_session(profile)
    return render(
        request,
        "workflow/researchers.html",
        page_context(
            request,
            {
                "researchers": researcher_repository.list_researchers_for_team(team_id=team_id, approved_only=True),
                "teams": researcher_repository.list_teams(),
                "can_manage_researchers": _can_manage(request),
            },
        ),
    )
