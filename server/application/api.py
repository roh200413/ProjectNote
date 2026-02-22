"""HTTP API entrypoints.

API handlers are defined in `server.application.views` today.
This module provides a clear API surface and is the import point for routing.
"""

from server.application.views import (
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
    research_note_detail_api,
    research_note_update_api,
    research_notes_api,
    researchers_api,
    signature_api,
    signup_api,
)

__all__ = [
    "admin_table_truncate_api",
    "admin_tables_api",
    "admin_teams_api",
    "admin_users_api",
    "dashboard_summary",
    "data_updates_api",
    "final_download_api",
    "frontend_bootstrap",
    "health",
    "project_management_api",
    "projects",
    "research_note_detail_api",
    "research_note_update_api",
    "research_notes_api",
    "researchers_api",
    "signature_api",
    "signup_api",
]
