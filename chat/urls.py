from django.urls import path
from . import views

urlpatterns = [
    path('start/', views.start_convo, name='start_convo'),
    path('<int:convo_id>/', views.get_conversation, name='get_conversation'),
    path('', views.conversations, name='conversations'),
    path('get-user-list/', views.user_list, name='user_list')
]