from django.urls import path
from . import views

urlpatterns = [
    path('<str:username>/', views.get_conversation, name='get_conversation'),

    path('add-message/<str:username>/', views.add_message, name='add message'),
    path('<int:id>/message/', views.delete_message, name='delete message'),
    path('', views.conversations, name='conversations'),
]
