from django.urls import path
from .views import *

urlpatterns = [
    path('posts/', PostsApiView.as_view()),
]