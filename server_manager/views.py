from django.shortcuts import render

# Create your views here.

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status

from .models import ServerConfig
from .serializers import ServerSerializer
from .ssh_service import test_ssh_connection


class CreateServerView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ServerSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(user=request.user)

            return Response({
                "success": True,
                "message": "Server saved successfully.",
                "data": serializer.data
            })

        return Response(serializer.errors, status=400)


class GetServerView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        server = ServerConfig.objects.filter(user=request.user, is_active=True).first()

        if not server:
            return Response({
                "success": False,
                "message": "No server configured."
            })

        return Response({
            "success": True,
            "data": ServerSerializer(server).data
        })


class TestConnectionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        host = request.data.get("host")
        port = request.data.get("ssh_port", 22)
        username = request.data.get("username")
        password = request.data.get("password")

        success, result = test_ssh_connection(host, port, username, password)

        if success:
            return Response({
                "success": True,
                "message": "Connection successful",
                "output": result
            })

        return Response({
            "success": False,
            "message": "Connection failed",
            "error": result
        }, status=400)