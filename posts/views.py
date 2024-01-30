from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from .serializers import *


class PostsApiViewSet(ModelViewSet):
    queryset = Post.actives.all()
    serializer_class = PostSerializer

    def get_queryset(self):
        all_of_posts = Post.actives.all()
        user = self.request.user
        following_posts = Post.actives.filter(author__in=user.following.all())
        queryset = following_posts | all_of_posts
        return queryset

class StoriesApiViewSet(ModelViewSet):
    queryset = Story.objects.all()
    serializer_class = StorySerializer

    def list(self, request, *args, **kwargs):
        following_users = request.user.following.all()
        following_stories = Story.objects.filter(author__in=following_users)
        serializer = self.get_serializer(following_stories, many=True)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        return Response({'detail': 'Method not allowed.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


class PostCommentView(APIView):
    def get(self, request, pk, *args, **kwargs):
        post_comments = Post.actives.get(pk=pk).comments.all()
        serializer = CommentSerializer(post_comments, many=True)
        return Response(serializer.data)
