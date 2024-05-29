from django.urls import path
from .views import SeenNotificationApiView

urlpatterns = [
    path('seen/<pk>/', SeenNotificationApiView.as_view())
]
