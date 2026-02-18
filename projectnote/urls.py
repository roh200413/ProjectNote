from django.urls import path

from projectnote import views

urlpatterns = [
    path("login", views.login_page),
    path("logout", views.logout_page),
    path("api/v1/health", views.health),
    path("api/v1/frontend/bootstrap", views.frontend_bootstrap),
    path("api/v1/dashboard/summary", views.dashboard_summary),
    path("api/v1/projects", views.projects),
    path("api/v1/project-management", views.project_management_api),
    path("api/v1/projects", views.researchers_api),
    path("api/v1/data-updates", views.data_updates_api),
    path("api/v1/final-download", views.final_download_api),
    path("api/v1/signatures", views.signature_api),
    path("api/v1/research-notes", views.research_notes_api),
    path("api/v1/research-notes/<str:note_id>", views.research_note_detail_api),
    path("api/v1/research-notes/<str:note_id>/update", views.research_note_update_api),
    path("frontend/workflows", views.workflow_home_page),
    path("frontend/admin", views.admin_page),
    path("frontend/projects/create", views.project_create_page),
    path("frontend/projects/<str:project_id>", views.project_detail_page),
    path("frontend/my-page", views.my_page),
    path("frontend/my-page/signature", views.update_my_signature),
    path("frontend/projects", views.projects),
    path("frontend/data-updates", views.data_updates_page),
    path("frontend/final-download", views.final_download_page),
    path("frontend/signatures", views.signature_page),
    path("frontend/research-notes", views.research_notes_page),
    path("frontend/research-notes/<str:note_id>", views.research_note_detail_page),
    path("frontend/research-notes/<str:note_id>/viewer", views.research_note_viewer_page),
]
