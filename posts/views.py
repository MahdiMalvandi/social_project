from django.contrib.contenttypes.models import ContentType
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
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


class PostStoryInteractionBaseView(APIView):
    """
    Base API view for handling interactions (like, comment) on posts and stories.
    """

    def _validate_post_or_story(self, post_or_story, pk):
        """
        Validate 'post_or_story' parameter and retrieve the object.

        Parameters:
        - `post_or_story`: 'post' or 'story' to specify the type.
        - `pk`: Primary key of the post or story.

        Returns:
        - Object: Post or Story object.
        """
        object_model = Story if post_or_story == 'story' else Post
        try:
            return object_model.actives.get(pk=pk)
        except object_model.DoesNotExist:
            raise NotFound("Object not found")

    def _get_content_type(self, object):
        """
        Get ContentType for the object.

        Parameters:
        - `object`: Post or Story object.

        Returns:
        - ContentType: ContentType instance.
        """
        return ContentType.objects.get_for_model(object)


class LikeApiView(PostStoryInteractionBaseView):
    """
    API view for handling likes and dislikes on posts and stories.
    """

    def post(self, request, post_or_story, pk):
        """
        Handles liking/disliking posts or stories.

        Parameters:
        - `post_or_story`: 'post' or 'story' to specify the type.
        - `pk`: Primary key of the post or story.

        Returns:
        - Response with relevant data and status code.
        """

        user = request.user

        # Validate 'post_or_story' parameter
        if post_or_story not in ['post', 'story']:
            return Response('"post_or_story" should be either a "post" or a "story"',
                            status=status.HTTP_400_BAD_REQUEST)

        # Get the object based on 'post_or_story' and 'pk'
        object = self._validate_post_or_story(post_or_story, pk)

        # Get ContentType for the object
        content_type = self._get_content_type(object)

        # Check if the user has already liked the object
        like = Like.objects.filter(user=user, content_type=content_type, object_id=object.pk)

        if like.exists():  # If user has liked, remove the like
            like.delete()
            is_liked = False
        else:  # If user has not liked, add a like
            Like.objects.create(
                user=user,
                content_type=content_type,
                object_id=object.pk
            )
            is_liked = True

        data = {
            'likes_count': object.likes.count(),
            'detail': 'success',
            'is_liked': is_liked
        }

        return Response(data, status=status.HTTP_204_NO_CONTENT)


class CommentsApiView(PostStoryInteractionBaseView):
    """
    API view for handling comments on posts and stories.
    """

    def get(self, request, post_or_story, pk):
        """
        Retrieve comments for a post or story.

        Parameters:
        - `post_or_story`: 'post' or 'story' to specify the type.
        - `pk`: Primary key of the post or story.

        Returns:
        - Response with comments data and status code.
        """
        user = request.user

        # Validate 'post_or_story' parameter
        if post_or_story not in ['post', 'story']:
            return Response('"post_or_story" should be either a "post" or a "story"',
                            status=status.HTTP_400_BAD_REQUEST)

        # Get the object based on 'post_or_story' and 'pk'
        object = self._validate_post_or_story(post_or_story, pk)

        # Get ContentType for the object
        content_type = self._get_content_type(object)

        # Retrieve comments
        comments = Comment.objects.filter(content_type=content_type, object_id=object.id, replies=None)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, post_or_story, pk):
        """
        Create a new comment on a post or story.

        Parameters:
        - `post_or_story`: 'post' or 'story' to specify the type.
        - `pk`: Primary key of the post or story.

        Returns:
        - Response with comment data and status code.
        """
        user = request.user

        # Validate 'post_or_story' parameter
        if post_or_story not in ['post', 'story']:
            return Response('"post_or_story" should be either a "post" or a "story"',
                            status=status.HTTP_400_BAD_REQUEST)

        # Get the object based on 'post_or_story' and 'pk'
        object = self._validate_post_or_story(post_or_story, pk)

        # Get ContentType for the object
        content_type = self._get_content_type(object)

        # Create a new comment
        data = {
            'replies': request.data.get('replies'),
            'content_type': content_type.pk,
            'object_id': object.id,
            'body': request.data['body']
        }
        serializer = CommentCreateUpdateSerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Return response
        response = {
            'message': 'success',
            'comments': CommentSerializer(object.comments.all(), many=True).data
        }
        return Response(response, status=status.HTTP_201_CREATED)
