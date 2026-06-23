from django.urls import path
from . import views

urlpatterns = [
    path("health/", views.HealthView.as_view(), name="health"),
    path("chat/", views.ChatView.as_view(), name="chat"),
    path("sessions/<uuid:session_id>/", views.SessionHistoryView.as_view(), name="session-history"),
]
