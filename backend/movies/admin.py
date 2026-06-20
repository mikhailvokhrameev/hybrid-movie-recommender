from django.contrib import admin
from .models import Movie, ChatSession


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ("serial_name", "content_type", "director", "release_date", "age_rating")
    list_filter = ("content_type",)
    search_fields = ("serial_name", "director", "description")


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ("session_id", "turn_count", "created_at", "updated_at")
    readonly_fields = ("session_id", "created_at", "updated_at")
