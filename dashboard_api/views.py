
# Create your models here.

from datetime import date
import psutil

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status

from apps_manager.models import App


class DashboardSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        user_apps = App.objects.filter(user=user)

        total_apps = user_apps.count()
        running_apps = user_apps.filter(status='running').count()
        stopped_apps = user_apps.filter(status='stopped').count()
        pending_apps = user_apps.filter(status='pending').count()
        failed_apps = user_apps.filter(status='failed').count()

        today = date.today()
        deployments_today = user_apps.filter(created_at__date=today).count()

        cpu_usage = psutil.cpu_percent(interval=0.5)
        ram_usage = psutil.virtual_memory().percent
        disk_usage = psutil.disk_usage('/').percent

        return Response({
            "success": True,
            "message": "Dashboard summary fetched successfully.",
            "data": {
                "total_apps": total_apps,
                "running_apps": running_apps,
                "stopped_apps": stopped_apps,
                "pending_apps": pending_apps,
                "failed_apps": failed_apps,
                "cpu_usage": cpu_usage,
                "ram_usage": ram_usage,
                "disk_usage": disk_usage,
                "deployments_today": deployments_today,
            }
        }, status=status.HTTP_200_OK)