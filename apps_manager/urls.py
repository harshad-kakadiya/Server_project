from django.urls import path
from .views import (
    AppDetailView,
    AppListView,
    CreateAppView,
    DeployTestView,
    DeployAppView,
    AppLogsView,
    AppStatusView,
    AppStopView,
    AppStartView,
    AppRestartView,
)

urlpatterns = [
    path('', AppListView.as_view(), name='app-list'),
    path('create/', CreateAppView.as_view(), name='app-create'),

    # Task 5 (optional - debug use)
    path('deploy-test/', DeployTestView.as_view(), name='app-deploy-test'),

    # Task 6 (IMPORTANT)
    path('<int:pk>/deploy/', DeployAppView.as_view(), name='app-deploy'),

    path('<int:pk>/', AppDetailView.as_view(), name='app-detail'),
    
    path('<int:pk>/logs/', AppLogsView.as_view(), name='app-logs'),
    
    path('<int:pk>/status/', AppStatusView.as_view(), name='app-status'),
    path('<int:pk>/stop/', AppStopView.as_view(), name='app-stop'),
    path('<int:pk>/start/', AppStartView.as_view(), name='app-start'),
    path('<int:pk>/restart/', AppRestartView.as_view(), name='app-restart'),
]