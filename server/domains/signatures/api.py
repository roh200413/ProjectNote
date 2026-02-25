from datetime import datetime, timezone
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods

from server.application.web_support import login_required_page, page_context, signature_repository


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
        return JsonResponse(signature_repository.read_signature())
    payload = signature_repository.update_signature(
        signed_by=request.POST.get("signed_by", ""), status=request.POST.get("status", "valid")
    )
    return JsonResponse(payload)


@require_GET
@ensure_csrf_cookie
@login_required_page
def final_download_page(request):
    return render(
        request,
        "workflow/final_download.html",
        page_context(request, {"report_name": "projectnote-final-report.pdf"}),
    )


@require_GET
@ensure_csrf_cookie
@login_required_page
def signature_page(request):
    return render(request, "workflow/signatures.html", page_context(request, {"signature": signature_repository.read_signature()}))


@require_GET
@ensure_csrf_cookie
@login_required_page
def my_page(request):
    profile = request.session.get("user_profile", {}).copy()
    profile["signature"] = profile.get("signature_data_url", "")
    return render(request, "workflow/my_page.html", page_context(request, {"profile": profile}))


@require_http_methods(["POST"])
@login_required_page
def update_my_signature(request):
    signature_data_url = request.POST.get("signature_data_url", "")
    if not signature_data_url.startswith("data:image/"):
        return JsonResponse({"message": "유효한 이미지 데이터가 아닙니다."}, status=400)

    profile = request.session.get("user_profile", {}).copy()
    profile["signature_data_url"] = signature_data_url
    request.session["user_profile"] = profile
    return JsonResponse({"message": "서명이 업데이트되었습니다."})
