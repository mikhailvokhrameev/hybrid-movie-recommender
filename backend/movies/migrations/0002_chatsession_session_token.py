import movies.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("movies", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="chatsession",
            name="session_token",
            field=models.CharField(
                db_index=True,
                default=movies.models.generate_token,
                max_length=64,
            ),
        ),
    ]
