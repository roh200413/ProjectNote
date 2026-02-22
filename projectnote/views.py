"""Legacy compatibility module.

Prefer new entrypoints:
- API: projectnote.server.interfaces.http.api.*
- Web pages: projectnote.client.interfaces.web
- Router: projectnote.server.interfaces.http.router
"""

from projectnote.client.interfaces.web import (  # noqa: F401
    admin_dashboard_page,
    admin_login_page,
    admin_page,
    admin_tables_page,
    admin_teams_page,
    admin_users_page,
    data_updates_page,
    final_download_page,
    login_page,
    logout_page,
    my_page,
    project_create_page,
    project_detail_page,
    project_management_page,
    researchers_page,
    research_note_detail_page,
    research_note_viewer_page,
    research_notes_page,
    signature_page,
    signup_page,
    update_my_signature,
    workflow_home_page,
)
from projectnote.server.interfaces.http.api import (  # noqa: F401
    admin_table_truncate_api,
    admin_tables_api,
    admin_teams_api,
    admin_users_api,
    dashboard_summary,
    data_updates_api,
    final_download_api,
    frontend_bootstrap,
    health,
    project_management_api,
    projects,
    researchers_api,
    research_note_detail_api,
    research_note_update_api,
    research_notes_api,
    signature_api,
    signup_api,
)
