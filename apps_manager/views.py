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