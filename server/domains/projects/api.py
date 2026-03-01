import uuid

from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods

from .models import Project
from server.application.web_support import (
    json_uuid_validation_error,
    login_required_page,
    page_context,
    effective_user_profile,
    project_repository,
    project_service,
    admin_repository,
    research_note_repository,
    dashboard_counts,
)


@require_GET
def projects(request):
    org_id = request.GET.get("org_id")
    if org_id:
        try:
            uuid.UUID(org_id)
        except ValueError:
            return json_uuid_validation_error("org_id", org_id)
    return JsonResponse(project_repository.list_projects(), safe=False)


@require_http_methods(["GET", "POST"])
def project_management_api(request):
    if request.method == "GET":
        profile = effective_user_profile(request) or {}
        return JsonResponse(project_repository.visible_projects_for_user(profile), safe=False)
    payload = request.POST.copy()
    profile = effective_user_profile(request) or {}
    team_id = profile.get("team_id")
    if team_id:
        payload["company_id"] = str(team_id)
    project = project_service.create_project(payload, effective_user_profile(request) or {})
    return JsonResponse(project, status=201)


@require_GET
@ensure_csrf_cookie
@login_required_page
def project_management_page(request):
    profile = effective_user_profile(request) or {}
    return render(request, "workflow/projects.html", page_context(request, {"projects": project_repository.visible_projects_for_user(profile)}))


@require_GET
@ensure_csrf_cookie
@login_required_page
def project_create_page(request):
    return render(
        request,
        "workflow/project_create.html",
        page_context(
            request,
            {"user_groups": admin_repository.user_groups_for_selection((effective_user_profile(request) or {}).get("team_id"))},
        ),
    )


@require_GET
@ensure_csrf_cookie
@login_required_page
def project_detail_page(request, project_id: str):
    profile = effective_user_profile(request) or {}
    if not project_repository.can_view_project(project_id, profile):
        raise Http404("Project not found")
    try:
        project = project_repository.project_to_dict(Project.objects.get(id=project_id))
    except Project.DoesNotExist as exc:
        raise Http404("Project not found") from exc

    note_ids = project_repository.project_note_ids(project_id)
    all_notes = research_note_repository.list_research_notes()
    project_notes = [note for note in all_notes if note["id"] in note_ids]
    selected_note = project_notes[0] if project_notes else None
    selected_note_files = research_note_repository.list_note_files(selected_note["id"]) if selected_note else []
    return render(
        request,
        "workflow/project_detail.html",
        page_context(
            request,
            {
                "project": project,
                "project_notes": project_notes,
                "researcher_groups": project_repository.project_researcher_groups(project_id),
                "selected_note": selected_note,
                "selected_note_files": selected_note_files,
            },
        ),
    )




@require_GET
@ensure_csrf_cookie
@login_required_page
def project_researchers_page(request, project_id: str):
    profile = effective_user_profile(request) or {}
    if not project_repository.can_view_project(project_id, profile):
        raise Http404("Project not found")
    try:
        project = project_repository.project_to_dict(Project.objects.get(id=project_id))
    except Project.DoesNotExist as exc:
        raise Http404("Project not found") from exc

    researcher_groups = project_repository.project_researcher_groups(project_id)
    existing_member_ids = {
        member["id"]
        for group in researcher_groups
        for member in group.get("members", [])
    }
    raw_team_groups = admin_repository.user_groups_for_selection((effective_user_profile(request) or {}).get("team_id"))
    filtered_team_groups = []
    for group in raw_team_groups:
        filtered_members = [
            member
            for member in group.get("members", [])
            if member.get("id") not in existing_member_ids and not bool(member.get("is_owner", False))
        ]
        if filtered_members:
            filtered_team_groups.append({**group, "members": filtered_members, "lead": filtered_members[0]["name"]})

    return render(
        request,
        "workflow/project_researchers.html",
        page_context(
            request,
            {
                "project": project,
                "researcher_groups": researcher_groups,
                "team_user_groups": filtered_team_groups,
                "can_manage_project_members": project_repository.can_manage_project_members(project_id, profile),
            },
        ),
    )



@require_GET
@ensure_csrf_cookie
@login_required_page
def project_research_notes_page(request, project_id: str):
    profile = effective_user_profile(request) or {}
    if not project_repository.can_view_project(project_id, profile):
        raise Http404("Project not found")
    try:
        project = project_repository.project_to_dict(Project.objects.get(id=project_id))
    except Project.DoesNotExist as exc:
        raise Http404("Project not found") from exc

    note_ids = project_repository.project_note_ids(project_id)
    all_notes = research_note_repository.list_research_notes()
    project_notes = [note for note in all_notes if note["id"] in note_ids]

    file_rows = []
    for note in project_notes:
        for file in research_note_repository.list_note_files(note["id"]):
            file_rows.append({
                "note_title": note["title"],
                "name": file["name"],
                "format": file["format"],
                "created": file["created"],
                "author": file["author"],
                "note_id": note["id"],
            })

    return render(
        request,
        "workflow/project_research_notes.html",
        page_context(
            request,
            {
                "project": project,
                "project_notes": project_notes,
                "project_files": file_rows,
                "note_count": len(project_notes),
                "file_count": len(file_rows),
            },
        ),
    )



@require_http_methods(["POST"])
def project_update_api(request, project_id: str):
    payload = request.POST.copy()
    try:
        updated = project_repository.update_project(project_id, {
            "name": payload.get("name", ""),
            "manager": payload.get("manager", ""),
            "organization": payload.get("organization", ""),
            "code": payload.get("code", ""),
            "description": payload.get("description", ""),
            "start_date": payload.get("start_date", ""),
            "end_date": payload.get("end_date", ""),
            "status": payload.get("status", "draft"),
        })
    except ValueError as exc:
        return JsonResponse({"detail": str(exc)}, status=404)
    return JsonResponse(updated)


@require_http_methods(["POST"])
def project_add_researcher_api(request, project_id: str):
    profile = effective_user_profile(request) or {}
    if not project_repository.can_manage_project_members(project_id, profile):
        return JsonResponse({"detail": "권한이 없습니다."}, status=403)

    user_id = request.POST.get("user_id", "")
    if not str(user_id).isdigit():
        return JsonResponse({"detail": "유효한 연구원을 선택하세요."}, status=400)

    try:
        project_repository.add_project_member(project_id, int(user_id))
    except ValueError as exc:
        return JsonResponse({"detail": str(exc)}, status=400)

    return JsonResponse({
        "message": "우리팀 연구원을 프로젝트에 추가했습니다.",
        "researcher_groups": project_repository.project_researcher_groups(project_id),
    })


@require_http_methods(["POST"])
def project_remove_researcher_api(request, project_id: str):
    profile = effective_user_profile(request) or {}
    if not project_repository.can_manage_project_members(project_id, profile):
        return JsonResponse({"detail": "권한이 없습니다."}, status=403)

    user_id = request.POST.get("user_id", "")
    if not str(user_id).isdigit():
        return JsonResponse({"detail": "유효한 연구원을 선택하세요."}, status=400)

    try:
        project_repository.remove_project_member(project_id, int(user_id))
    except ValueError as exc:
        return JsonResponse({"detail": str(exc)}, status=400)

    return JsonResponse({
        "message": "프로젝트 연구원을 제외했습니다.",
        "researcher_groups": project_repository.project_researcher_groups(project_id),
    })

@require_GET
def dashboard_summary(_request):
    return JsonResponse(dashboard_counts())


@require_GET
@ensure_csrf_cookie
@login_required_page
def workflow_home_page(request):
    cards = [
        {"title": "프로젝트 생성", "href": "/frontend/projects/create", "description": "신규 프로젝트를 생성합니다."},
        {"title": "프로젝트 관리", "href": "/frontend/projects", "description": "생성된 프로젝트 목록/상세를 관리합니다."},
        {"title": "연구자 관리", "href": "/frontend/researchers", "description": "연구자 등록 및 소속/역할 정보를 관리합니다."},
        {"title": "데이터 업데이트", "href": "/frontend/data-updates", "description": "데이터 업데이트 이력을 기록합니다."},
    ]
    projects = project_repository.list_projects()
    current_name = (effective_user_profile(request) or {}).get("name", "")
    managed_projects = [project for project in projects if project.get("manager") == current_name]
    return render(
        request,
        "workflow/home.html",
        page_context(request, {"cards": cards, "managed_projects": managed_projects}),
    )
