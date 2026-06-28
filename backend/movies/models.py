import secrets
import uuid

from django.db import models
from django.utils import timezone
from pgvector.django import VectorField, HnswIndex


def generate_token():
    return secrets.token_urlsafe(32)


class Movie(models.Model):
    serial_name = models.CharField(max_length=500, db_index=True)
    genres = models.JSONField(default=list)
    content_type = models.CharField(max_length=50)
    country = models.JSONField(default=list)
    actors = models.JSONField(default=list)
    director = models.CharField(max_length=255, blank=True, default="")
    age_rating = models.FloatField(null=True, blank=True)
    studio_name = models.CharField(max_length=500, blank=True, default="")
    release_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True, default="")
    url = models.URLField(max_length=500, unique=True)
    embedding = VectorField(dimensions=768, null=True, blank=True)

    class Meta:
        indexes = [
            HnswIndex(
                name="movie_embedding_hnsw",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            ),
        ]

    def __str__(self):
        return self.serial_name


class ChatSession(models.Model):
    session_id = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    session_token = models.CharField(max_length=64, default=generate_token, db_index=True)
    preference_vector = VectorField(dimensions=768, null=True, blank=True)
    preferences = models.JSONField(default=dict)
    history = models.JSONField(default=list)
    turn_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["updated_at"]),
        ]

    def is_expired(self):
        return timezone.now() - self.created_at > timezone.timedelta(hours=24)

    def __str__(self):
        return f"Session {self.session_id} (turn {self.turn_count})"
