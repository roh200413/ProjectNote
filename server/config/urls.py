from django.urls import path

from server.application import api
from server.domains.admin import http as admin_http
from server.domains.auth import http as auth_http
from server.domains.dashboard import http as dashboard_http
from server.domains.data_updates import http as data_updates_http
from server.domains.projects import http as projects_http
from server.domains.research_notes import http as research_notes_http
from server.domains.researchers import http as researchers_http
from server.domains.signatures import http as signatures_http

urlpatterns = [
    path("login", auth_http.login_page),
    path("admin/login", auth_http.admin_login_page),
    path("signup", auth_http.signup_page),
    path("logout", auth_http.logout_page),
    path("api/v1/auth/signup", api.signup_api),
    path("api/v1/health", api.health),
    path("api/v1/frontend/bootstrap", api.frontend_bootstrap),
    path("api/v1/dashboard/summary", api.dashboard_summary),
    path("api/v1/projects", api.projects),
    path("api/v1/project-management", api.project_management_api),
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
    path("frontend/workflows", dashboard_http.workflow_home_page),
    path("frontend/admin", admin_http.admin_page),
    path("frontend/admin/dashboard", admin_http.admin_dashboard_page),
    path("frontend/admin/teams", admin_http.admin_teams_page),
    path("frontend/admin/users", admin_http.admin_users_page),
    path("frontend/admin/tables", admin_http.admin_tables_page),
    path("frontend/projects", projects_http.project_management_page),
    path("frontend/projects/create", projects_http.project_create_page),
    path("frontend/projects/<str:project_id>", projects_http.project_detail_page),
    path("frontend/my-page", signatures_http.my_page),
    path("frontend/my-page/signature", signatures_http.update_my_signature),
    path("frontend/researchers", researchers_http.researchers_page),
    path("frontend/data-updates", data_updates_http.data_updates_page),
    path("frontend/final-download", signatures_http.final_download_page),
    path("frontend/signatures", signatures_http.signature_page),
    path("frontend/research-notes", research_notes_http.research_notes_page),
    path("frontend/research-notes/<str:note_id>", research_notes_http.research_note_detail_page),
    path("frontend/research-notes/<str:note_id>/viewer", research_notes_http.research_note_viewer_page),
]
