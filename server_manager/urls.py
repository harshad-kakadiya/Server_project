from django.urls import path
from .views import CreateServerView, GetServerView, TestConnectionView

urlpatterns = [
    path('create/', CreateServerView.as_view()),
    path('get/', GetServerView.as_view()),
    path('test/', TestConnectionView.as_view()),
]