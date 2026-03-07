from django.urls import path

from server.application import api
from server.application.frontend_cutover import frontend_cutover_redirect
from server.application.openapi import openapi_json_api
from server.domains.admin import api as admin_api
from server.domains.auth import api as auth_api
from server.domains.data_updates import api as data_updates_api
from server.domains.projects import api as projects_api
from server.domains.research_notes import api as research_notes_api
from server.domains.researchers import api as researchers_api
from server.domains.signatures import api as signatures_api

urlpatterns = [
    path("api/v1/auth/signup", api.signup_api),
    path("api/v1/auth/login", auth_api.login_api),
    path("api/v1/auth/logout", auth_api.logout_api),
    path("api/v1/auth/me", auth_api.me_api),
    path("api/v1/health", api.health),
    path("api/v1/openapi.json", openapi_json_api),
    path("api/v1/frontend/bootstrap", api.frontend_bootstrap),
    path("api/v1/dashboard/summary", api.dashboard_summary),
    path("api/v1/projects", api.projects),
    path("api/v1/project-management", api.project_management_api),
    path("api/v1/projects/<str:project_id>/update", projects_api.project_update_api),
    path("api/v1/projects/<str:project_id>/cover", projects_api.project_cover_update_api),
    path("api/v1/projects/<str:project_id>/cover/print", projects_api.project_cover_print_api),
    path("api/v1/projects/<str:project_id>/researchers", projects_api.project_add_researcher_api),
    path("api/v1/projects/<str:project_id>/researchers/remove", projects_api.project_remove_researcher_api),
    path("api/v1/projects/<str:project_id>/research-files", projects_api.project_research_files_api),
    path("api/v1/projects/<str:project_id>/research-notes/upload", projects_api.project_upload_research_note_api),
    path("api/v1/projects/<str:project_id>/research-notes/export-pdf", projects_api.project_research_notes_export_pdf_api),
    path("api/v1/researchers", api.researchers_api),
    path("api/v1/data-updates", api.data_updates_api),
    path("api/v1/final-download", api.final_download_api),
    path("api/v1/signatures", api.signature_api),
    path("api/v1/admin/teams", api.admin_teams_api),
    path("api/v1/admin/users", api.admin_users_api),
    path("api/v1/admin/tables", api.admin_tables_api),
    path("api/v1/admin/tables/<str:table_name>/truncate", api.admin_table_truncate_api),
    path("api/v1/research-notes", api.research_notes_api),
    path("api/v1/research-notes/<str:note_id>", api.research_note_detail_api),
    path("api/v1/research-notes/<str:note_id>/update", api.research_note_update_api),
    path("api/v1/research-notes/<str:note_id>/files", research_notes_api.research_note_files_api),
    path("api/v1/research-notes/<str:note_id>/viewer-export-pdf", research_notes_api.research_note_viewer_export_pdf_api),
    path("api/v1/research-notes/<str:note_id>/files/<str:file_id>/update", research_notes_api.research_note_file_update_api),

    path("admin/login", auth_api.admin_login_page),

    path("login", auth_api.login_page),
    path("signup", auth_api.signup_page),
    path("logout", auth_api.logout_page),

    # Legacy template runtime (preserved for UI parity, consumed by apps/web iframe wrapper).
    path("legacy/frontend/admin", admin_api.admin_page),
    path("legacy/frontend/admin/dashboard", admin_api.admin_dashboard_page),
    path("legacy/frontend/admin/teams", admin_api.admin_teams_page),
    path("legacy/frontend/admin/users", admin_api.admin_users_page),
    path("legacy/frontend/admin/tables", admin_api.admin_tables_page),
    path("legacy/frontend/workflows", projects_api.workflow_home_page),
    path("legacy/frontend/projects", projects_api.project_management_page),
    path("legacy/frontend/projects/create", projects_api.project_create_page),
    path("legacy/frontend/projects/<str:project_id>", projects_api.project_detail_page),
    path("legacy/frontend/projects/<str:project_id>/researchers", projects_api.project_researchers_page),
    path("legacy/frontend/projects/<str:project_id>/research-notes", projects_api.project_research_notes_page),
    path("legacy/frontend/projects/<str:project_id>/research-notes/print", projects_api.project_research_notes_print_page),
    path("legacy/frontend/my-page", signatures_api.my_page),
    path("legacy/frontend/researchers", researchers_api.researchers_page),
    path("legacy/frontend/integrations/github", researchers_api.github_integrations_page),
    path("legacy/frontend/integrations/collaboration", researchers_api.collaboration_integrations_page),
    path("legacy/frontend/data-updates", data_updates_api.data_updates_page),
    path("legacy/frontend/final-download", signatures_api.final_download_page),
    path("legacy/frontend/signatures", signatures_api.signature_page),
    path("legacy/frontend/research-notes", research_notes_api.research_notes_page),
    path("legacy/frontend/research-notes/<str:note_id>", research_notes_api.research_note_detail_page),
    path("legacy/frontend/research-notes/<str:note_id>/viewer", research_notes_api.research_note_viewer_page),
    path("legacy/frontend/research-notes/<str:note_id>/cover", research_notes_api.research_note_cover_page),
    path("legacy/frontend/research-notes/<str:note_id>/printable", research_notes_api.research_note_printable_page),
    path("legacy/frontend/research-notes/<str:note_id>/files/<str:file_id>/content", research_notes_api.research_note_file_content_page),

    # Legacy action/content endpoints kept stable.
    path("frontend/my-page/signature", signatures_api.update_my_signature),
    path("frontend/my-page/research-note/upload", signatures_api.upload_my_research_note),
    path("frontend/research-notes/<str:note_id>/files/<str:file_id>/content", research_notes_api.research_note_file_content_page),

    # Runtime frontend cutover to React app.
    path("frontend", frontend_cutover_redirect),
    path("frontend/<path:legacy_path>", frontend_cutover_redirect),
]
