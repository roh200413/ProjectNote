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
