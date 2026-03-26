
# Register your models here.

from django.contrib import admin
from .models import App


@admin.register(App)
class AppAdmin(admin.ModelAdmin):
    list_display = ('id', 'app_name', 'framework', 'source_type', 'port', 'status', 'user', 'created_at') 
    search_fields = ('app_name', 'framework', 'source_type', 'domain', 'user__username', 'user__email')
    list_filter = ('framework', 'source_type', 'status', 'https_enabled', 'is_public')