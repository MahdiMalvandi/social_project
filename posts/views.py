from django.contrib.contenttypes.models import ContentType
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from .serializers import *
from django.contrib.contenttypes.models import ContentType


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

    # def list(self, request, *args, **kwargs):
    #     following_users = request.user.following.all()
    #     following_stories = Story.actives.filter(author__in=following_users)
    #     serializer = self.get_serializer(following_stories, many=True)
    #     return Response(serializer.data)

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


class LikeApiView(APIView):
    """
    API view for handling likes and dislikes on posts and stories.
    """

    def post(self, request, post_or_story, pk):
        """
        Handle POST requests for liking/disliking posts or stories.

        Parameters:
        - `post_or_story`: Specify whether the object is a 'post' or a 'story'.
        - `pk`: Primary key of the post or story.

        Returns:
        - Response with relevant data and status code.
        """

        user = request.user

        # Validate 'post_or_story' parameter
        if post_or_story not in ['post', 'story']:
            return Response('"post_or_story" should be either a "post" or a "story"',
                            status=status.HTTP_400_BAD_REQUEST)

        # Get object based on 'post_or_story' and 'pk'
        if post_or_story == 'story':
            try:
                object = Story.actives.get(pk=pk)
            except Story.DoesNotExist:
                return Response("Story not found", status=status.HTTP_404_NOT_FOUND)
        else:
            try:
                object = Post.actives.get(pk=pk)
            except Post.DoesNotExist:
                return Response('Post not found', status=status.HTTP_404_NOT_FOUND)

        # Get ContentType for the object
        content_type = ContentType.objects.get_for_model(object)

        # Check if the user has already liked the object
        like = Like.objects.filter(user=user, content_type=content_type, object_id=object.pk)

        if like.exists():  # If user has liked, remove the like
            like.first().delete()
            data = {
                'likes_count': object.likes.count(),
                'detail': 'success',
                'is_liked': False
            }
        else:  # If user has not liked, add a like
            like_obj = Like.objects.create(
                user=user,
                content_type=content_type,
                object_id=object.pk
            )
            data = {
                'likes_count': object.likes.count(),
                'detail': 'success',
                'is_liked': True
            }

        return Response(data, status=status.HTTP_204_NO_CONTENT)
