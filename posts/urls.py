from django.urls import path
from .views import *
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('posts', PostsApiViewSet, basename='posts')
router.register('stories', StoriesApiViewSet, basename='stories', )
urlpatterns = [
    path('like/<post_or_story>/<pk>/', LikeApiView.as_view(), name='like'),
    path('comments/<post_or_story>/<pk>/', CommentsApiView.as_view(), name='comments'),
    path('tags/popular/', PopularTagsAPIView.as_view(), name='popular tags'),
    path('search/', SearchApiView.as_view(), name='search'),
    path('save/<int:post_id>/', SavedPostsApiView.as_view(), name='save post'),
    path('save/', SavedPostsListApiView.as_view(), name='saved post list'),
    path('posts/get-by-tag/<tag_name>/', GetPostsByTagApiView.as_view())
]
urlpatterns += router.urls
