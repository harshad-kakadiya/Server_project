from rest_framework import serializers
from .models import ServerConfig


class ServerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServerConfig
        fields = "__all__"
        read_only_fields = ['user']