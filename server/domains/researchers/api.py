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
        or role in {"관리자", "admin"}
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


@require_http_methods(["GET", "POST"])
@login_required_page
def researchers_api(request):
    profile = effective_user_profile(request) or {}
    team_id = _resolve_team_id_from_session(profile)

    if request.method == "GET":
        action = request.GET.get("action", "").strip()
        if action == "unassigned":
            query = request.GET.get("q", "").strip()
            return JsonResponse(researcher_repository.list_unassigned_users(query), safe=False)
        if action == "pending_for_my_team":
            return JsonResponse(researcher_repository.list_pending_users_by_team_id(team_id), safe=False)
        return JsonResponse(researcher_repository.list_researchers_for_team(team_id=team_id, approved_only=True), safe=False)

    action = request.POST.get("action", "create").strip()
    if action == "create":
        try:
            created = researcher_repository.create_researcher(dict(request.POST))
        except ValueError as exc:
            return JsonResponse({"detail": str(exc)}, status=400)
        return JsonResponse(created, status=201)

    if action == "verify_id":
        payload = researcher_repository.verify_unassigned_user_id(request.POST.get("username", ""))
        return JsonResponse(payload)

    if not _can_manage(request):
        return JsonResponse({"detail": "관리 권한이 없습니다."}, status=403)

    try:
        if action == "assign_team":
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
                role_raw = request.POST.get("role", "").strip()

                # ✅ repository가 기대하는 값으로 정규화: admin / member
                if role_raw in {"admin", "관리자"}:
                    role = "admin"
                elif role_raw in {"member", "일반"}:
                    role = "member"
                else:
                    return JsonResponse({"detail": "권한 값이 올바르지 않습니다."}, status=400)

                # ✅ 관리자 최대 3명 제한 (admin 기준)
                if role == "admin":
                    admin_count = researcher_repository.count_admins_by_team_id(team_id)
                    if admin_count >= 3:
                        return JsonResponse({"detail": "관리자는 팀당 최대 3명까지만 지정할 수 있습니다."}, status=400)

                payload = researcher_repository.grant_role(user_id, role)
            elif action == "remove_from_company":
                payload = researcher_repository.remove_from_company(user_id, team_id)
            else:
                return JsonResponse({"detail": "지원하지 않는 작업입니다."}, status=400)
    except ValueError as exc:
        return JsonResponse({"detail": str(exc)}, status=400)
    return JsonResponse(payload)


@require_GET
@ensure_csrf_cookie
@login_required_page
def researchers_page(request):
    profile = effective_user_profile(request) or {}
    team_id = _resolve_team_id_from_session(profile)
    return render(
        request,
        "workflow/researchers.html",
        page_context(
            request,
            {
                "researchers": researcher_repository.list_researchers_for_team(team_id=team_id, approved_only=True),
                "pending_researchers": researcher_repository.list_pending_users_by_team_id(team_id),
                "teams": researcher_repository.list_teams(),
                "can_manage_researchers": _can_manage(request),
            },
        ),
    )
