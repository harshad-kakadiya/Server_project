from django.db import models

# Create your models here.

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class ServerConfig(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    name = models.CharField(max_length=100)
    host = models.CharField(max_length=255)
    ssh_port = models.IntegerField(default=22)
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=255)  # MVP only

    deploy_base_path = models.CharField(max_length=255, default="/home/ubuntu/apps")

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name