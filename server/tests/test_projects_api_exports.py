import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.config.settings")

import django

django.setup()

from server.domains.projects import api as projects_api


def test_projects_api_exports_required_route_handlers() -> None:
    """URLs referenced in server/config/urls.py must always exist on projects_api."""
    required_handlers = [
        "project_update_api",
        "project_add_researcher_api",
        "project_remove_researcher_api",
        "project_upload_research_note_api",
    ]

    missing = [name for name in required_handlers if not hasattr(projects_api, name)]
    assert not missing, f"Missing projects_api handlers: {missing}"

    for name in required_handlers:
        assert callable(getattr(projects_api, name)), f"projects_api.{name} is not callable"
