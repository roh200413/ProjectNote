from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET

from server.application.web_support import login_required_page, page_context, repository


@require_GET
def dashboard_summary(_request):
    return JsonResponse(repository.dashboard_counts())


@require_GET
@ensure_csrf_cookie
@login_required_page
def workflow_home_page(request):
    cards = [
        {"title": "프로젝트 생성", "href": "/frontend/projects/create", "description": "신규 프로젝트를 생성합니다."},
        {"title": "프로젝트 관리", "href": "/frontend/projects", "description": "생성된 프로젝트 목록/상세를 관리합니다."},
        {"title": "연구자 관리", "href": "/frontend/researchers", "description": "연구자 등록 및 소속/역할 정보를 관리합니다."},
        {"title": "데이터 업데이트", "href": "/frontend/data-updates", "description": "데이터 업데이트 이력을 기록합니다."},
        {"title": "연구노트 최종 다운로드", "href": "/frontend/final-download", "description": "최종 산출물 생성 상태를 확인합니다."},
        {"title": "사인 업데이트", "href": "/frontend/signatures", "description": "최신 서명 상태를 갱신합니다."},
        {"title": "My Page", "href": "/frontend/my-page", "description": "내 상세 정보와 전자서명을 확인합니다."},
        {"title": "ADMIN", "href": "/frontend/admin", "description": "운영 지표와 최근 액션을 조회합니다."},
    ]
    return render(request, "workflow/home.html", page_context(request, {"cards": cards}))
