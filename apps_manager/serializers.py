from rest_framework import serializers
from .models import App


class CreateAppSerializer(serializers.ModelSerializer):
    class Meta:
        model = App
        fields = [
            'app_name',
            'framework',
            'source_type',
            'repository_url',
            'build_command',
            'start_command',
            'port',
            'domain',
            'https_enabled',
            'is_public',
        ]

    def validate_app_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("App name is required.")
        return value

    def validate_port(self, value):
        if value < 1 or value > 65535:
            raise serializers.ValidationError("Port must be between 1 and 65535.")
        return value

    def validate(self, attrs):
        request = self.context.get('request')
        user = request.user

        app_name = attrs.get('app_name')
        source_type = attrs.get('source_type')
        repository_url = attrs.get('repository_url')
        port = attrs.get('port')

        # only github support for now
        if source_type != 'github':
            raise serializers.ValidationError({
                "source_type": "Currently only GitHub source is supported."
            })

        if source_type == 'github' and not repository_url:
            raise serializers.ValidationError({
                "repository_url": "Repository URL is required for GitHub source."
            })

        if App.objects.filter(user=user, app_name__iexact=app_name).exists():
            raise serializers.ValidationError({
                "app_name": "You already have an app with this name."
            })

        if App.objects.filter(user=user, port=port).exists():
            raise serializers.ValidationError({
                "port": "You already have an app using this port."
            })

        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        return App.objects.create(user=user, **validated_data)


class AppListSerializer(serializers.ModelSerializer):
    class Meta:
        model = App
        fields = [
            'id',
            'app_name',
            'framework',
            'source_type',
            'repository_url',
            'build_command',
            'start_command',
            'port',
            'domain',
            'https_enabled',
            'is_public',
            'status',
            'created_at',
            'updated_at',
        ]