from django.urls import path
from .views import (
    AppDetailView,
    AppListView,
    CreateAppView,
    DeployTestView,
    DeployAppView,
)

urlpatterns = [
    path('', AppListView.as_view(), name='app-list'),
    path('create/', CreateAppView.as_view(), name='app-create'),

    # Task 5 (optional - debug use)
    path('deploy-test/', DeployTestView.as_view(), name='app-deploy-test'),

    # Task 6 (IMPORTANT)
    path('<int:pk>/deploy/', DeployAppView.as_view(), name='app-deploy'),

    path('<int:pk>/', AppDetailView.as_view(), name='app-detail'),
]