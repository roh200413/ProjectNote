from django.urls import path

from projectnote import views

urlpatterns = [
    path("api/v1/health", views.health),
    path("api/v1/frontend/bootstrap", views.frontend_bootstrap),
    path("api/v1/dashboard/summary", views.dashboard_summary),
    path("api/v1/projects", views.projects),
    path("api/v1/research-notes", views.research_notes_api),
    path("api/v1/research-notes/<str:note_id>", views.research_note_detail_api),
    path("frontend/research-notes", views.research_notes_page),
    path("frontend/research-notes/<str:note_id>", views.research_note_detail_page),
]
