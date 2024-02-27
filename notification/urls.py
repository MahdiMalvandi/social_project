from django.urls import path
from .views import SeenNotificationApiView

urlpatterns = [
    path('seen/', SeenNotificationApiView.as_view())
]
