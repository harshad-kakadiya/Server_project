from django.shortcuts import render

# Create your views here.

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from server_manager.models import ServerConfig
from server_manager.ssh_service import run_ssh_command

from .models import App
from .serializers import CreateAppSerializer, AppListSerializer
from .deploy_service import deploy_repository


class CreateAppView(generics.CreateAPIView):
    serializer_class = CreateAppSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        app = serializer.save()

        return Response({
            "success": True,
            "message": "App created successfully.",
            "data": AppListSerializer(app).data
        }, status=status.HTTP_201_CREATED)


class AppListView(generics.ListAPIView):
    serializer_class = AppListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return App.objects.filter(user=self.request.user).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        return Response({
            "success": True,
            "message": "Apps fetched successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class AppDetailView(generics.RetrieveAPIView):
    serializer_class = AppListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return App.objects.filter(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        app = self.get_object()
        serializer = self.get_serializer(app)

        return Response({
            "success": True,
            "message": "App details fetched successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class DeployTestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        server = ServerConfig.objects.filter(
            user=request.user, is_active=True
        ).order_by('-id').first()

        if not server:
            return Response(
                {
                    "success": False,
                    "message": "No active server configured.",
                    "error": "No active server configured.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        ok, result = run_ssh_command(
            server.host,
            server.ssh_port,
            server.username,
            server.password,
            "whoami",
        )

        if ok:
            return Response(
                {
                    "success": True,
                    "message": "Remote command executed successfully.",
                    "output": result,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "success": False,
                "message": "Remote command execution failed.",
                "error": result,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
        
class DeployAppView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            app = App.objects.get(pk=pk, user=request.user)
        except App.DoesNotExist:
            return Response({
                "success": False,
                "message": "App not found."
            }, status=status.HTTP_404_NOT_FOUND)

        if not app.repository_url:
            return Response({
                "success": False,
                "message": "Repository URL is missing for this app."
            }, status=status.HTTP_400_BAD_REQUEST)

        success, result, deployment = deploy_repository(app, request.user)

        if success:
            return Response({
                "success": True,
                "message": "Repository deployed successfully.",
                "data": {
                    "deployment_id": deployment.id,
                    "app_id": app.id,
                    "status": deployment.status,
                    "output": result
                }
            }, status=status.HTTP_200_OK)

        return Response({
            "success": False,
            "message": "Repository deployment failed.",
            "error": result,
            "deployment_id": deployment.id if deployment else None
        }, status=status.HTTP_400_BAD_REQUEST)
 
class AppLogsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            app = App.objects.get(pk=pk, user=request.user)
        except App.DoesNotExist:
            return Response({
                "success": False,
                "message": "App not found."
            }, status=status.HTTP_404_NOT_FOUND)

        server = ServerConfig.objects.filter(
            user=request.user,
            is_active=True
        ).order_by('-id').first()

        if not server:
            return Response({
                "success": False,
                "message": "No active server configured."
            }, status=status.HTTP_400_BAD_REQUEST)

        command = "bash -lc 'docker logs --tail 100 app 2>&1'"

        success, result = run_ssh_command(
            server.host,
            server.ssh_port,
            server.username,
            server.password,
            command
        )

        return Response({
            "success": True,
            "message": "Logs fetched successfully.",
            "data": {
                "app_id": app.id,
                "app_name": app.app_name,
                "command": command,
                "logs": result or "No logs found."
            }
        }, status=status.HTTP_200_OK)
        
class AppStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            app = App.objects.get(pk=pk, user=request.user)
        except App.DoesNotExist:
            return Response({
                "success": False,
                "message": "App not found."
            }, status=status.HTTP_404_NOT_FOUND)

        server = ServerConfig.objects.filter(
            user=request.user,
            is_active=True
        ).order_by('-id').first()

        if not server:
            return Response({
                "success": False,
                "message": "No active server configured."
            }, status=status.HTTP_400_BAD_REQUEST)

        container_name = app.container_name
        command = f'bash -lc \'docker ps -a --filter "name=^{app_name}$" --format "{{{{.Status}}}}"\' 2>&1'

        success, result = run_ssh_command(
            server.host,
            server.ssh_port,
            server.username,
            server.password,
            command
        )

        if not success:
            return Response({
                "success": False,
                "message": "Failed to fetch app status.",
                "error": result
            }, status=status.HTTP_400_BAD_REQUEST)

        docker_status = (result or "").strip()

        if not docker_status:
            actual_status = "not_found"
        elif docker_status.lower().startswith("up"):
            actual_status = "running"
        elif docker_status.lower().startswith("exited"):
            actual_status = "stopped"
        else:
            actual_status = docker_status

        app.status = actual_status if actual_status in ["running", "stopped", "failed", "pending", "building"] else app.status
        app.save()

        return Response({
            "success": True,
            "message": "App status fetched successfully.",
            "data": {
                "app_id": app.id,
                "app_name": app.app_name,
                "db_status": app.status,
                "docker_status": docker_status,
                "actual_status": actual_status
            }
        }, status=status.HTTP_200_OK)


class AppStopView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            app = App.objects.get(pk=pk, user=request.user)
        except App.DoesNotExist:
            return Response({
                "success": False,
                "message": "App not found."
            }, status=status.HTTP_404_NOT_FOUND)

        server = ServerConfig.objects.filter(
            user=request.user,
            is_active=True
        ).order_by('-id').first()

        if not server:
            return Response({
                "success": False,
                "message": "No active server configured."
            }, status=status.HTTP_400_BAD_REQUEST)

        app_name = app.app_name.strip().replace(" ", "-").lower()
        command = f'docker stop "{app_name}" 2>&1'

        success, result = run_ssh_command(
            server.host,
            server.ssh_port,
            server.username,
            server.password,
            command
        )

        if not success:
            return Response({
                "success": False,
                "message": "Failed to stop app.",
                "error": result
            }, status=status.HTTP_400_BAD_REQUEST)

        app.status = 'stopped'
        app.save()

        return Response({
            "success": True,
            "message": "App stopped successfully.",
            "data": {
                "app_id": app.id,
                "app_name": app.app_name,
                "output": result
            }
        }, status=status.HTTP_200_OK)


class AppStartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            app = App.objects.get(pk=pk, user=request.user)
        except App.DoesNotExist:
            return Response({
                "success": False,
                "message": "App not found."
            }, status=status.HTTP_404_NOT_FOUND)

        server = ServerConfig.objects.filter(
            user=request.user,
            is_active=True
        ).order_by('-id').first()

        if not server:
            return Response({
                "success": False,
                "message": "No active server configured."
            }, status=status.HTTP_400_BAD_REQUEST)

        app_name = app.app_name.strip().replace(" ", "-").lower()
        command = f'docker start "{app_name}" 2>&1'

        success, result = run_ssh_command(
            server.host,
            server.ssh_port,
            server.username,
            server.password,
            command
        )

        if not success:
            return Response({
                "success": False,
                "message": "Failed to start app.",
                "error": result
            }, status=status.HTTP_400_BAD_REQUEST)

        app.status = 'running'
        app.save()

        return Response({
            "success": True,
            "message": "App started successfully.",
            "data": {
                "app_id": app.id,
                "app_name": app.app_name,
                "output": result
            }
        }, status=status.HTTP_200_OK)


class AppRestartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            app = App.objects.get(pk=pk, user=request.user)
        except App.DoesNotExist:
            return Response({
                "success": False,
                "message": "App not found."
            }, status=status.HTTP_404_NOT_FOUND)

        server = ServerConfig.objects.filter(
            user=request.user,
            is_active=True
        ).order_by('-id').first()

        if not server:
            return Response({
                "success": False,
                "message": "No active server configured."
            }, status=status.HTTP_400_BAD_REQUEST)

        app_name = app.app_name.strip().replace(" ", "-").lower()
        command = f'docker restart "{app_name}" 2>&1'

        success, result = run_ssh_command(
            server.host,
            server.ssh_port,
            server.username,
            server.password,
            command
        )

        if not success:
            return Response({
                "success": False,
                "message": "Failed to restart app.",
                "error": result
            }, status=status.HTTP_400_BAD_REQUEST)

        app.status = 'running'
        app.save()

        return Response({
            "success": True,
            "message": "App restarted successfully.",
            "data": {
                "app_id": app.id,
                "app_name": app.app_name,
                "output": result
            }
        }, status=status.HTTP_200_OK)

class DeleteAppView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        try:
            app = App.objects.get(pk=pk, user=request.user)
        except App.DoesNotExist:
            return Response({
                "success": False,
                "message": "App not found."
            }, status=status.HTTP_404_NOT_FOUND)

        server = ServerConfig.objects.filter(
            user=request.user,
            is_active=True
        ).order_by('-id').first()

        if not server:
            return Response({
                "success": False,
                "message": "No active server configured."
            }, status=status.HTTP_400_BAD_REQUEST)

        app_name = app.app_name.strip().replace(" ", "-").lower()
        remote_base = server.deploy_base_path.rstrip("/")
        remote_path = f"{remote_base}/{app_name}"
        image_name = f"{app_name}:latest"

        command = (
            f'bash -lc \''
            f'docker rm -f "{container_name}" 2>/dev/null || true; '
            f'docker rmi -f "{image_name}" 2>/dev/null || true; '
            f'rm -rf "{remote_path}"'
            f'\''
        )

        success, result = run_ssh_command(
            server.host,
            server.ssh_port,
            server.username,
            server.password,
            command
        )

        if not success:
            return Response({
                "success": False,
                "message": "Failed to delete app resources from server.",
                "error": result
            }, status=status.HTTP_400_BAD_REQUEST)

        app.delete()

        return Response({
            "success": True,
            "message": "App deleted successfully.",
            "data": {
                "app_name": app_name,
                "server_output": result or "App resources removed successfully."
            }
        }, status=status.HTTP_200_OK)