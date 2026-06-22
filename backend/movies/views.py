from datetime import datetime

from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Movie


class HealthView(APIView):
    def get(self, request):
        return Response({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "catalog_size": Movie.objects.count(),
        })
