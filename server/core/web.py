from functools import wraps

from django.http import JsonResponse
from django.shortcuts import redirect


def page_context(request, extra: dict | None = None) -> dict:
    context = {
        "current_user": request.session.get(
            "user_profile",
            {
                "name": "게스트",
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
        user_profile = request.session.get("user_profile")
        if not user_profile:
            next_url = request.get_full_path()
            return redirect(f"/login?next={next_url}")
        if user_profile.get("is_super_admin"):
            return redirect("/frontend/admin/dashboard")
        return view_func(request, *args, **kwargs)

    return _wrapped


def admin_required_page(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user_profile = request.session.get("user_profile")
        if not user_profile or not user_profile.get("is_super_admin"):
            next_url = request.get_full_path()
            return redirect(f"/admin/login?next={next_url}")
        return view_func(request, *args, **kwargs)

    return _wrapped


def save_login_session(request, username: str, user: dict[str, str]) -> None:
    request.session["user_profile"] = {
        "username": username,
        "name": user["name"],
        "role": user["role"],
        "email": user["email"],
        "organization": user["organization"],
        "major": user["major"],
        "team": user.get("team", "-"),
        "is_super_admin": bool(user.get("is_super_admin", False)),
        "signature_data_url": request.session.get("user_profile", {}).get("signature_data_url", ""),
    }


def json_uuid_validation_error(field: str, raw_input: str) -> JsonResponse:
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
