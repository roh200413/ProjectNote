import uuid
from datetime import datetime, timezone
from functools import wraps

from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
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
        "summary": "AI 자동평가 고도화와 현장 검증 히스토리를 관리하는 연구노트입니다.",
        "last_updated_at": "2026-02-18T11:03:00+09:00",
    },
    {
        "id": "da3a50af-d4e9-40ad-8b3f-472cd2666726",
        "title": "FE TIM Monorepo 연동 연구노트",
        "owner": "최재혁",
        "project_code": "PN-2026-FE-TIM",
        "period": "2026.01.01 ~ 2026.12.31",
        "files": 368,
        "members": 6,
        "summary": "연구노트 서비스의 프론트엔드 구조 및 UI 리뉴얼 작업 로그",
        "last_updated_at": "2026-02-17T09:40:00+09:00",
    },
]

PROJECTS = [
    {
        "id": "cbce1902-d86b-4be4-af3f-cd9c011868e0",
        "name": "원전 AI 자동평가 고도화",
        "status": "active",
        "manager": "김기수",
        "organization": "딥테크딥스",
    },
    {
        "id": "53316220-cc3f-48f0-b9eb-1aaf55a48f86",
        "name": "연구노트 FE 고도화",
        "status": "draft",
        "manager": "최재혁",
        "organization": "ProjectNote Lab",
    },
]

PROJECT_NOTE_MAP = {
    "cbce1902-d86b-4be4-af3f-cd9c011868e0": ["7fe010e7-402a-40d7-b818-84dada03d8ee"],
    "53316220-cc3f-48f0-b9eb-1aaf55a48f86": ["da3a50af-d4e9-40ad-8b3f-472cd2666726"],
}

PROJECT_RESEARCHER_GROUPS = {
    "cbce1902-d86b-4be4-af3f-cd9c011868e0": [
        {
            "group": "AI 모델링팀",
            "lead": "김기수",
            "members": [
                {
                    "name": "김기수",
                    "role": "PI",
                    "organization": "딥테크딥스",
                    "major": "R&D",
                    "contribution": "모델 기획",
                },
                {
                    "name": "노승희",
                    "role": "관리자",
                    "organization": "딥테크딥스",
                    "major": "MLOps",
                    "contribution": "배포/운영 관리",
                },
            ],
        },
        {
            "group": "현장 검증팀",
            "lead": "박서준",
            "members": [
                {
                    "name": "박서준",
                    "role": "책임연구원",
                    "organization": "원전검사원",
                    "major": "품질검증",
                    "contribution": "현장 테스트",
                },
                {
                    "name": "정유나",
                    "role": "연구원",
                    "organization": "원전검사원",
                    "major": "QA",
                    "contribution": "결과 검증",
                },
            ],
        },
    ],
    "53316220-cc3f-48f0-b9eb-1aaf55a48f86": [
        {
            "group": "프론트엔드팀",
            "lead": "최재혁",
            "members": [
                {
                    "name": "최재혁",
                    "role": "리드",
                    "organization": "ProjectNote Lab",
                    "major": "Web",
                    "contribution": "디자인 시스템 설계",
                },
                {
                    "name": "한민지",
                    "role": "연구원",
                    "organization": "ProjectNote Lab",
                    "major": "뷰어 엔진",
                    "contribution": "문서 뷰어 구현",
                },
            ],
        }
    ],
}

NOTE_FILE_MAP = {
    "7fe010e7-402a-40d7-b818-84dada03d8ee": [
        {
            "id": "file-1",
            "name": "[2026.02.13] deep-ai-kr/fe-tim-monorepo_git",
            "author": "최재혁",
            "format": "git",
            "created": "2026.02.14 / 12:01 AM",
        },
        {
            "id": "file-2",
            "name": "[2026.02.12] deep-ai-kr/ect-auto_git.pdf",
            "author": "노승희",
            "format": "pdf",
            "created": "2026.02.13 / 10:11 AM",
        },
    ],
    "da3a50af-d4e9-40ad-8b3f-472cd2666726": [
        {
            "id": "file-3",
            "name": "[2026.02.08] workspace-setting-ui.png",
            "author": "한민지",
            "format": "png",
            "created": "2026.02.09 / 08:30 PM",
        }
    ],
}

NOTE_FOLDERS = {
    "7fe010e7-402a-40d7-b818-84dada03d8ee": ["[DEEPTECH - DOCS]", "[DEEPTECH - WEB]", "[DEEPTECH - AI]"],
    "da3a50af-d4e9-40ad-8b3f-472cd2666726": ["[FE - REFS]", "[FE - UI]"],
}

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

DEMO_USERS = {
    "admin": {
        "password": "admin1234",
        "name": "노승희",
        "role": "관리자",
        "email": "paul@deep-ai.kr",
        "organization": "(주)딥아이",
        "major": "R&D",
    }
}


def _find_note(note_id: str) -> dict:
    for note in RESEARCH_NOTES:
        if note["id"] == note_id:
            return note
    raise Http404("Research note not found")


def _find_project(project_id: str) -> dict:
    for project in PROJECTS:
        if project["id"] == project_id:
            return project
    raise Http404("Project not found")


def _page_context(request, extra: dict | None = None) -> dict:
    context = {
        "current_user": request.session.get(
            "user_profile",
            {
                "name": "노승희",
                "role": "관리자",
            },
        )
    }
    if extra:
        context.update(extra)
    return context


def login_required_page(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.session.get("user_profile"):
            next_url = request.get_full_path()
            return redirect(f"/login?next={next_url}")
        return view_func(request, *args, **kwargs)

    return _wrapped


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


@require_http_methods(["GET", "POST"])
def login_page(request):
    if request.method == "GET":
        if request.session.get("user_profile"):
            return redirect("/frontend/workflows")
        return render(request, "auth/login.html", {"error": "", "next": request.GET.get("next", "")})

    username = request.POST.get("username", "").strip()
    password = request.POST.get("password", "")
    next_url = request.POST.get("next", "")
    user = DEMO_USERS.get(username)
    if not user or user["password"] != password:
        return render(
            request,
            "auth/login.html",
            {"error": "아이디 또는 비밀번호가 올바르지 않습니다.", "next": next_url},
            status=401,
        )

    request.session["user_profile"] = {
        "username": username,
        "name": user["name"],
        "role": user["role"],
        "email": user["email"],
        "organization": user["organization"],
        "major": user["major"],
    }
    if next_url.startswith("/"):
        return redirect(next_url)
    return redirect("/frontend/workflows")


@require_GET
def logout_page(request):
    request.session.pop("user_profile", None)
    return redirect("/login")


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
        "organization": request.POST.get("organization", "미지정"),
    }
    PROJECTS.append(project)
    PROJECT_NOTE_MAP[project["id"]] = []
    PROJECT_RESEARCHER_GROUPS[project["id"]] = []
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


@require_http_methods(["POST"])
def research_note_update_api(request, note_id: str):
    note = _find_note(note_id)
    note["title"] = request.POST.get("title", note["title"])
    note["summary"] = request.POST.get("summary", note["summary"])
    note["last_updated_at"] = datetime.now(timezone.utc).isoformat()
    return JsonResponse({"message": "연구노트가 업데이트되었습니다.", "note": note})


@require_GET
@ensure_csrf_cookie
@login_required_page
def workflow_home_page(_request):
    cards = [
        {"title": "프로젝트 생성", "href": "/frontend/projects/create", "description": "신규 프로젝트를 생성합니다."},
        {"title": "프로젝트 관리", "href": "/frontend/projects", "description": "생성된 프로젝트 목록과 상세를 관리합니다."},
        {"title": "연구자 추가", "href": "/frontend/researchers", "description": "연구 참여 인력 정보를 등록합니다."},
        {"title": "데이터 업데이트", "href": "/frontend/data-updates", "description": "데이터 업데이트 이력을 기록합니다."},
        {"title": "연구노트 최종 다운로드", "href": "/frontend/final-download", "description": "최종 산출물 생성 상태를 확인합니다."},
        {"title": "사인 업데이트", "href": "/frontend/signatures", "description": "최신 서명 상태를 갱신합니다."},
        {"title": "My Page", "href": "/frontend/my-page", "description": "내 상세 정보와 전자서명을 확인합니다."},
        {"title": "ADMIN", "href": "/frontend/admin", "description": "운영 지표와 최근 액션을 조회합니다."},
    ]
    return render(_request, "workflow/home.html", _page_context(_request, {"cards": cards}))


@require_GET
@ensure_csrf_cookie
@login_required_page
def project_management_page(_request):
    return render(_request, "workflow/projects.html", _page_context(_request, {"projects": PROJECTS}))


@require_GET
@ensure_csrf_cookie
@login_required_page
def project_create_page(_request):
    return render(_request, "workflow/project_create.html", _page_context(_request))


@require_GET
@ensure_csrf_cookie
@login_required_page
def project_detail_page(_request, project_id: str):
    project = _find_project(project_id)
    note_ids = PROJECT_NOTE_MAP.get(project_id, [])
    project_notes = [note for note in RESEARCH_NOTES if note["id"] in note_ids]
    selected_note = project_notes[0] if project_notes else None
    return render(
        _request,
        "workflow/project_detail.html",
        _page_context(
            _request,
            {
                "project": project,
                "project_notes": project_notes,
                "researcher_groups": PROJECT_RESEARCHER_GROUPS.get(project_id, []),
                "selected_note": selected_note,
                "selected_note_files": NOTE_FILE_MAP.get(selected_note["id"], []) if selected_note else [],
            },
        ),
    )


@require_GET
@ensure_csrf_cookie
@login_required_page
def researchers_page(_request):
    return render(_request, "workflow/researchers.html", _page_context(_request, {"researchers": RESEARCHERS}))


@require_GET
@ensure_csrf_cookie
@login_required_page
def data_updates_page(_request):
    return render(_request, "workflow/data_updates.html", _page_context(_request, {"updates": DATA_UPDATES}))


@require_GET
@ensure_csrf_cookie
@login_required_page
def final_download_page(_request):
    return render(
        _request,
        "workflow/final_download.html",
        _page_context(_request, {"report_name": "projectnote-final-report.pdf"}),
    )


@require_GET
@ensure_csrf_cookie
@login_required_page
def signature_page(_request):
    return render(_request, "workflow/signatures.html", _page_context(_request, {"signature": SIGNATURE_STATE}))


@require_GET
@ensure_csrf_cookie
@login_required_page
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
    return render(_request, "workflow/admin.html", _page_context(_request, {"metrics": metrics, "recent": recent}))


@require_GET
@ensure_csrf_cookie
@login_required_page
def my_page(_request):
    profile = _request.session.get("user_profile", {}).copy()
    profile["signature"] = "서명"
    return render(_request, "workflow/my_page.html", _page_context(_request, {"profile": profile}))


@require_GET
@ensure_csrf_cookie
@login_required_page
def research_notes_page(_request):
    return render(_request, "research_notes/list.html", _page_context(_request, {"notes": RESEARCH_NOTES}))


@require_GET
@ensure_csrf_cookie
@login_required_page
def research_note_detail_page(_request, note_id: str):
    note = _find_note(note_id)
    return render(
        _request,
        "research_notes/detail.html",
        _page_context(
            _request,
            {
                "note": note,
                "files": NOTE_FILE_MAP.get(note_id, []),
                "folders": NOTE_FOLDERS.get(note_id, []),
            },
        ),
    )


@require_GET
@ensure_csrf_cookie
@login_required_page
def research_note_viewer_page(_request, note_id: str):
    note = _find_note(note_id)
    files = NOTE_FILE_MAP.get(note_id, [])
    return render(
        _request,
        "research_notes/viewer.html",
        _page_context(_request, {"note": note, "file": files[0] if files else None}),
    )
