from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class App(models.Model):
    FRAMEWORK_CHOICES = [
        ('fastapi', 'FastAPI'),
        ('flask', 'Flask'),
        ('django', 'Django'),
        ('express', 'Express'),
        ('react', 'React'),
        ('docker', 'Docker'),
        ('go', 'Go'),
        ('rust', 'Rust'),
    ]

    SOURCE_TYPE_CHOICES = [
        ('github', 'GitHub Repo'),
        ('docker_image', 'Docker Image'),
        ('manual_upload', 'Manual Upload'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('building', 'Building'),
        ('running', 'Running'),
        ('stopped', 'Stopped'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='apps')
    app_name = models.CharField(max_length=100)
    framework = models.CharField(max_length=30, choices=FRAMEWORK_CHOICES)
    source_type = models.CharField(max_length=30, choices=SOURCE_TYPE_CHOICES)
    repository_url = models.URLField(blank=True, null=True)
    build_command = models.CharField(max_length=255, blank=True, null=True)
    start_command = models.CharField(max_length=255, blank=True, null=True)
    port = models.PositiveIntegerField()
    domain = models.CharField(max_length=255, blank=True, null=True)
    https_enabled = models.BooleanField(default=False)
    is_public = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    container_name = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.app_name


class Deployment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('building', 'Building'),
        ('running', 'Running'),
        ('failed', 'Failed'),
    ]

    app = models.ForeignKey(App, on_delete=models.CASCADE, related_name='deployments')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    logs = models.TextField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.app.app_name} - {self.status}"