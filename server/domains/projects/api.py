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
    project_repository,
    project_service,
    researcher_repository,
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
        return JsonResponse(project_repository.list_projects(), safe=False)
    project = project_service.create_project(request.POST)
    return JsonResponse(project, status=201)


@require_GET
@ensure_csrf_cookie
@login_required_page
def project_management_page(request):
    return render(request, "workflow/projects.html", page_context(request, {"projects": project_repository.list_projects()}))


@require_GET
@ensure_csrf_cookie
@login_required_page
def project_create_page(request):
    return render(
        request,
        "workflow/project_create.html",
        page_context(request, {"researcher_groups": researcher_repository.researcher_groups_for_selection()}),
    )


@require_GET
@ensure_csrf_cookie
@login_required_page
def project_detail_page(request, project_id: str):
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
    try:
        project = project_repository.project_to_dict(Project.objects.get(id=project_id))
    except Project.DoesNotExist as exc:
        raise Http404("Project not found") from exc

    return render(
        request,
        "workflow/project_researchers.html",
        page_context(
            request,
            {
                "project": project,
                "researcher_groups": project_repository.project_researcher_groups(project_id),
            },
        ),
    )

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
    current_name = request.session.get("user_profile", {}).get("name", "")
    managed_projects = [project for project in projects if project.get("manager") == current_name]
    return render(
        request,
        "workflow/home.html",
        page_context(request, {"cards": cards, "managed_projects": managed_projects}),
    )
