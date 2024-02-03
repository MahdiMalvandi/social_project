from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from .serializers import *


class PostsApiViewSet(ModelViewSet):
    queryset = Post.actives.all()
    serializer_class = PostSerializer

    # def get_queryset(self):
    #     all_of_posts = Post.actives.all()
    #     user = self.request.user
    #     following_posts = Post.actives.filter(author__in=user.following.all())
    #     queryset = following_posts | all_of_posts
    #     return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return PostCreateUpdateSerializer
        return PostSerializer

    def create(self, request, *args, **kwargs):
        caption = request.data.get('caption', '')
        files_data = request.data.getlist('files', [])
        data = {'caption': caption, 'files': files_data}
        serializer = self.get_serializer(data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'success': True, 'detail': "post created successfully"}, status=status.HTTP_201_CREATED)


class StoriesApiViewSet(ModelViewSet):
    queryset = Story.actives.all()
    serializer_class = StorySerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return StoryCreateUpdateSerializer
        return StorySerializer

    def list(self, request, *args, **kwargs):
        following_users = request.user.following.all()
        following_stories = Story.objects.filter(author__in=following_users)
        serializer = self.get_serializer(following_stories, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        content = request.data.get('content', '')
        files_data = request.data.getlist('files', [])
        data = {'content': content, 'files': files_data}
        serializer = self.get_serializer(data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'success': True, 'detail': "story created successfully"}, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        return Response({'detail': 'Method not allowed.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


class PostCommentView(APIView):
    def get(self, request, pk, *args, **kwargs):
        post_comments = Post.actives.get(pk=pk).comments.all()
        serializer = CommentSerializer(post_comments, many=True)
        return Response(serializer.data)
