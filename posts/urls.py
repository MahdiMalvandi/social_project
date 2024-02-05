from django.urls import path
from .views import *
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('posts', PostsApiViewSet, basename='posts')
router.register('stories', StoriesApiViewSet, basename='stories', )
urlpatterns = [
    path('posts/<pk>/comments/', PostCommentView.as_view(), name='post comments'),
    path('like/<post_or_story>/<pk>/', LikeApiView.as_view(), name='like'),
]
urlpatterns += router.urls
