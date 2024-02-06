from django.urls import path
from .views import *
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('posts', PostsApiViewSet, basename='posts')
router.register('stories', StoriesApiViewSet, basename='stories', )
urlpatterns = [
    path('like/<post_or_story>/<pk>/', LikeApiView.as_view(), name='like'),
    path('comments/<post_or_story>/<pk>/', CommentsApiView.as_view(), name='comments')
]
urlpatterns += router.urls
