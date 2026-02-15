import uuid
from datetime import datetime, timezone

from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods


RESEARCH_NOTES = [
    {
        "id": "7fe010e7-402a-40d7-b818-84dada03d8ee",
        "title": "딥테크딥스 - 원자력발전소 증기발생기 전열관 와전류탐상검사 AI자동평가 기술 개발",
        "owner": "김기수",
        "project_code": "RS-2023-00262239",
        "period": "2023.06.01 ~ 2026.06.01",
        "files": 1109,
        "members": 17,
    },
    {
        "id": "da3a50af-d4e9-40ad-8b3f-472cd2666726",
        "title": "FE TIM Monorepo 연동 연구노트",
        "owner": "최재혁",
        "project_code": "PN-2026-FE-TIM",
        "period": "2026.01.01 ~ 2026.12.31",
        "files": 368,
        "members": 6,
    },
]

PROJECTS = [
    {
        "id": "cbce1902-d86b-4be4-af3f-cd9c011868e0",
        "name": "원전 AI 자동평가 고도화",
        "status": "active",
        "manager": "김기수",
    },
    {
        "id": "53316220-cc3f-48f0-b9eb-1aaf55a48f86",
        "name": "연구노트 FE 고도화",
        "status": "draft",
        "manager": "최재혁",
    },
]

RESEARCHERS = [
    {"id": "1", "name": "김기수", "role": "PI", "email": "kim@example.com"},
    {"id": "2", "name": "최재혁", "role": "연구원", "email": "choi@example.com"},
]

DATA_UPDATES = [
    {
        "id": "upd-1",
        "target": "연구노트 메타데이터",
        "status": "completed",
        "updated_at": "2026-02-18T11:03:00+09:00",
    }
]

SIGNATURE_STATE = {
    "last_signed_by": "김기수",
    "last_signed_at": "2026-02-18T11:10:00+09:00",
    "status": "valid",
}


def _find_note(note_id: str) -> dict:
    for note in RESEARCH_NOTES:
        if note["id"] == note_id:
            return note
    raise Http404("Research note not found")


def _json_uuid_validation_error(field: str, raw_input: str) -> JsonResponse:
    return JsonResponse(
        {
            "detail": [
                {
                    "type": "uuid_parsing",
                    "loc": ["query", field],
                    "msg": "Input should be a valid UUID.",
                    "input": raw_input,
                }
            ]
        },
        status=422,
    )


@require_GET
def health(_request):
    return JsonResponse({"status": "ok"})


@require_GET
def frontend_bootstrap(_request):
    return JsonResponse(
        {
            "api_name": "ProjectNote API",
            "api_version": "v1",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


@require_GET
def dashboard_summary(_request):
    return JsonResponse(
        {
            "organizations": 1,
            "projects": len(PROJECTS),
            "notes": len(RESEARCH_NOTES),
            "revisions": 0,
        }
    )


@require_GET
def projects(request):
    org_id = request.GET.get("org_id")

    if org_id:
        try:
            uuid.UUID(org_id)
        except ValueError:
            return _json_uuid_validation_error("org_id", org_id)

    return JsonResponse(PROJECTS, safe=False)


@require_http_methods(["GET", "POST"])
def project_management_api(request):
    if request.method == "GET":
        return JsonResponse(PROJECTS, safe=False)

    name = request.POST.get("name", "새 프로젝트")
    manager = request.POST.get("manager", "미지정")
    project = {
        "id": str(uuid.uuid4()),
        "name": name,
        "status": "draft",
        "manager": manager,
    }
    PROJECTS.append(project)
    return JsonResponse(project, status=201)


@require_http_methods(["GET", "POST"])
def researchers_api(request):
    if request.method == "GET":
        return JsonResponse(RESEARCHERS, safe=False)

    researcher = {
        "id": str(len(RESEARCHERS) + 1),
        "name": request.POST.get("name", "신규 연구원"),
        "role": request.POST.get("role", "연구원"),
        "email": request.POST.get("email", "unknown@example.com"),
    }
    RESEARCHERS.append(researcher)
    return JsonResponse(researcher, status=201)


@require_http_methods(["GET", "POST"])
def data_updates_api(request):
    if request.method == "GET":
        return JsonResponse(DATA_UPDATES, safe=False)

    update_item = {
        "id": f"upd-{len(DATA_UPDATES) + 1}",
        "target": request.POST.get("target", "연구데이터"),
        "status": request.POST.get("status", "queued"),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    DATA_UPDATES.append(update_item)
    return JsonResponse(update_item, status=201)


@require_GET
def final_download_api(_request):
    payload = {
        "format": "pdf",
        "status": "ready",
        "download_url": "/downloads/projectnote-final-report.pdf",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    return JsonResponse(payload)


@require_http_methods(["GET", "POST"])
def signature_api(request):
    if request.method == "GET":
        return JsonResponse(SIGNATURE_STATE)

    SIGNATURE_STATE["last_signed_by"] = request.POST.get("signed_by", SIGNATURE_STATE["last_signed_by"])
    SIGNATURE_STATE["last_signed_at"] = datetime.now(timezone.utc).isoformat()
    SIGNATURE_STATE["status"] = request.POST.get("status", "valid")
    return JsonResponse(SIGNATURE_STATE)


@require_GET
def research_notes_api(_request):
    return JsonResponse(RESEARCH_NOTES, safe=False)


@require_GET
def research_note_detail_api(_request, note_id: str):
    return JsonResponse(_find_note(note_id))


@require_GET
@ensure_csrf_cookie
def workflow_home_page(_request):
    cards = [
        {"title": "프로젝트 생성 및 관리", "href": "/frontend/projects", "description": "프로젝트를 생성하고 상태를 관리합니다."},
        {"title": "연구자 추가", "href": "/frontend/researchers", "description": "연구 참여 인력 정보를 등록합니다."},
        {"title": "데이터 업데이트", "href": "/frontend/data-updates", "description": "데이터 업데이트 이력을 기록합니다."},
        {"title": "연구노트 최종 다운로드", "href": "/frontend/final-download", "description": "최종 산출물 생성 상태를 확인합니다."},
        {"title": "사인 업데이트", "href": "/frontend/signatures", "description": "최신 서명 상태를 갱신합니다."},
        {"title": "ADMIN", "href": "/frontend/admin", "description": "운영 지표와 최근 액션을 조회합니다."},
    ]
    return render(_request, "workflow/home.html", {"cards": cards})


@require_GET
@ensure_csrf_cookie
def project_management_page(_request):
    return render(_request, "workflow/projects.html", {"projects": PROJECTS})


@require_GET
@ensure_csrf_cookie
def researchers_page(_request):
    return render(_request, "workflow/researchers.html", {"researchers": RESEARCHERS})


@require_GET
@ensure_csrf_cookie
def data_updates_page(_request):
    return render(_request, "workflow/data_updates.html", {"updates": DATA_UPDATES})


@require_GET
@ensure_csrf_cookie
def final_download_page(_request):
    return render(_request, "workflow/final_download.html", {"report_name": "projectnote-final-report.pdf"})


@require_GET
@ensure_csrf_cookie
def signature_page(_request):
    return render(_request, "workflow/signatures.html", {"signature": SIGNATURE_STATE})




@require_GET
@ensure_csrf_cookie
def admin_page(_request):
    metrics = {
        "projects": len(PROJECTS),
        "researchers": len(RESEARCHERS),
        "updates": len(DATA_UPDATES),
        "notes": len(RESEARCH_NOTES),
    }
    recent = [
        {"type": "last_signature", "value": SIGNATURE_STATE["last_signed_by"]},
        {"type": "last_project", "value": PROJECTS[-1]["name"]},
        {"type": "last_update", "value": DATA_UPDATES[-1]["target"]},
    ]
    return render(_request, "workflow/admin.html", {"metrics": metrics, "recent": recent})

@require_GET
@ensure_csrf_cookie
def research_notes_page(_request):
    return render(_request, "research_notes/list.html", {"notes": RESEARCH_NOTES})


@require_GET
@ensure_csrf_cookie
def research_note_detail_page(_request, note_id: str):
    note = _find_note(note_id)
    fake_files = [
        {"name": f"[2026.02.{idx:02d}] deep-ai-kr/fe-tim-monorepo_git", "author": "최재혁"}
        for idx in range(13, 8, -1)
    ]
    return render(
        _request,
        "research_notes/detail.html",
        {
            "note": note,
            "files": fake_files,
        },
    )
