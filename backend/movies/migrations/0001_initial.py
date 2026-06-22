import uuid

import pgvector.django.indexes
import pgvector.django.vector
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.RunSQL(
            "CREATE EXTENSION IF NOT EXISTS vector;",
            reverse_sql="DROP EXTENSION IF EXISTS vector;",
        ),
        migrations.CreateModel(
            name="Movie",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("serial_name", models.CharField(db_index=True, max_length=500)),
                ("genres", models.JSONField(default=list)),
                ("content_type", models.CharField(max_length=50)),
                ("country", models.JSONField(default=list)),
                ("actors", models.JSONField(default=list)),
                ("director", models.CharField(blank=True, default="", max_length=255)),
                ("age_rating", models.FloatField(blank=True, null=True)),
                (
                    "studio_name",
                    models.CharField(blank=True, default="", max_length=500),
                ),
                ("release_date", models.DateField(blank=True, null=True)),
                ("description", models.TextField(blank=True, default="")),
                ("url", models.URLField(max_length=500, unique=True)),
                (
                    "embedding",
                    pgvector.django.vector.VectorField(
                        blank=True, dimensions=768, null=True
                    ),
                ),
            ],
            options={
                "indexes": [
                    pgvector.django.indexes.HnswIndex(
                        ef_construction=64,
                        fields=["embedding"],
                        m=16,
                        name="movie_embedding_hnsw",
                        opclasses=["vector_cosine_ops"],
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="ChatSession",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "session_id",
                    models.UUIDField(db_index=True, default=uuid.uuid4, unique=True),
                ),
                (
                    "preference_vector",
                    pgvector.django.vector.VectorField(
                        blank=True, dimensions=768, null=True
                    ),
                ),
                ("preferences", models.JSONField(default=dict)),
                ("history", models.JSONField(default=list)),
                ("turn_count", models.IntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "indexes": [
                    models.Index(
                        fields=["updated_at"], name="movies_chats_updated_5765c7_idx"
                    ),
                ],
            },
        ),
    ]
