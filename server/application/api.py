"""HTTP API entrypoints grouped by domain."""

from server.domains.admin.api import (
    admin_table_truncate_api,
    admin_tables_api,
    admin_teams_api,
    admin_users_api,
)
from server.domains.auth.api import frontend_bootstrap, health, signup_api
from server.domains.dashboard.api import dashboard_summary
from server.domains.data_updates.api import data_updates_api
from server.domains.projects.api import project_management_api, projects
from server.domains.research_notes.api import (
    research_note_detail_api,
    research_note_update_api,
    research_notes_api,
)
from server.domains.researchers.api import researchers_api
from server.domains.signatures.api import final_download_api, signature_api

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
