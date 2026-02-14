import uuid
from datetime import datetime, timezone

from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET


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


def _find_note(note_id: str) -> dict:
    for note in RESEARCH_NOTES:
        if note["id"] == note_id:
            return note
    raise Http404("Research note not found")


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
    return JsonResponse({"organizations": 1, "projects": 2, "notes": len(RESEARCH_NOTES), "revisions": 0})


@require_GET
def projects(request):
    org_id = request.GET.get("org_id")

    if org_id:
        try:
            uuid.UUID(org_id)
        except ValueError:
            return JsonResponse(
                {
                    "detail": [
                        {
                            "type": "uuid_parsing",
                            "loc": ["query", "org_id"],
                            "msg": "Input should be a valid UUID.",
                            "input": org_id,
                        }
                    ]
                },
                status=422,
            )

    return JsonResponse([], safe=False)


@require_GET
def research_notes_api(_request):
    return JsonResponse(RESEARCH_NOTES, safe=False)


@require_GET
def research_note_detail_api(_request, note_id: str):
    return JsonResponse(_find_note(note_id))


@require_GET
def research_notes_page(_request):
    return render(_request, "research_notes/list.html", {"notes": RESEARCH_NOTES})


@require_GET
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
