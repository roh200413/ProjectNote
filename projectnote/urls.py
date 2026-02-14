from django.urls import path

from projectnote import views

urlpatterns = [
    path("api/v1/health", views.health),
    path("api/v1/frontend/bootstrap", views.frontend_bootstrap),
    path("api/v1/dashboard/summary", views.dashboard_summary),
    path("api/v1/projects", views.projects),
]
