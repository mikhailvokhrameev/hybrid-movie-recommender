from django.core.management.base import BaseCommand
from django.utils import timezone

from movies.models import ChatSession


class Command(BaseCommand):
    help = "Delete expired chat sessions (older than 24 hours)"

    def handle(self, *args, **options):
        cutoff = timezone.now() - timezone.timedelta(hours=24)
        count, _ = ChatSession.objects.filter(created_at__lt=cutoff).delete()
        self.stdout.write(
            self.style.SUCCESS(f"Deleted {count} expired sessions")
        )
