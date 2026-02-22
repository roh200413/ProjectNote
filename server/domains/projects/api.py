import uuid

from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods

from server.application.models import Project
from server.application.web_support import json_uuid_validation_error, login_required_page, page_context, service, repository


@require_GET
def projects(request):
    org_id = request.GET.get("org_id")
    if org_id:
        try:
            uuid.UUID(org_id)
        except ValueError:
            return json_uuid_validation_error("org_id", org_id)
    return JsonResponse(repository.list_projects(), safe=False)


@require_http_methods(["GET", "POST"])
def project_management_api(request):
    if request.method == "GET":
        return JsonResponse(repository.list_projects(), safe=False)
    project = service.create_project(request.POST)
    return JsonResponse(project, status=201)


@require_GET
@ensure_csrf_cookie
@login_required_page
def project_management_page(request):
    return render(request, "workflow/projects.html", page_context(request, {"projects": repository.list_projects()}))


@require_GET
@ensure_csrf_cookie
@login_required_page
def project_create_page(request):
    return render(
        request,
        "workflow/project_create.html",
        page_context(request, {"researcher_groups": repository.researcher_groups_for_selection()}),
    )


@require_GET
@ensure_csrf_cookie
@login_required_page
def project_detail_page(request, project_id: str):
    try:
        project = repository.project_to_dict(Project.objects.get(id=project_id))
    except Project.DoesNotExist as exc:
        raise Http404("Project not found") from exc

    note_ids = repository.project_note_ids(project_id)
    all_notes = repository.list_research_notes()
    project_notes = [note for note in all_notes if note["id"] in note_ids]
    selected_note = project_notes[0] if project_notes else None
    selected_note_files = repository.list_note_files(selected_note["id"]) if selected_note else []
    return render(
        request,
        "workflow/project_detail.html",
        page_context(
            request,
            {
                "project": project,
                "project_notes": project_notes,
                "researcher_groups": repository.project_researcher_groups(project_id),
                "selected_note": selected_note,
                "selected_note_files": selected_note_files,
            },
        ),
    )
