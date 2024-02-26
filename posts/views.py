from django.db.models import Count
from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from taggit.models import Tag

from .serializers import *
from django.contrib.contenttypes.models import ContentType


class PostsApiViewSet(ModelViewSet):
    queryset = Post.actives.all()
    serializer_class = PostSerializer
    pagination_class = PageNumberPagination

    """
    This view set handles the retrieval and creation of posts.

    - For creation, it accepts a POST request with a caption and optional files.
    - For retrieval, it lists all active posts.

    For creating a new post, use HTTP POST method with 'caption' and optional 'files' in the request body.
    """

    # region Retrieve and create posts
    def get_serializer_class(self):
        if self.action == 'create':
            return PostCreateUpdateSerializer
        return PostSerializer

    def get_queryset(self):
        all_of_posts = Post.actives.all()
        user = self.request.user
        following_posts = Post.actives.filter(author__in=user.following.all())
        queryset = following_posts | all_of_posts
        return queryset

    def create(self, request, *args, **kwargs):
        if request.data.get('caption') is None:
            return Response('The caption must not be empty', status=status.HTTP_400_BAD_REQUEST)
        if request.data.get('files') is None:
            return Response('There must be at least one file', status=status.HTTP_400_BAD_REQUEST)
        caption = request.data.get('caption', '')
        files_data = request.data.getlist('files', [])

        data = {'caption': caption, 'files': files_data}
        serializer = self.get_serializer(data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'success': True, 'detail': "post created successfully"}, status=status.HTTP_201_CREATED)
    # endregion


class StoriesApiViewSet(ModelViewSet):
    queryset = Story.actives.all()
    serializer_class = StorySerializer

    """
    This view set handles the retrieval and creation of stories.

    - For creation, it accepts a POST request with a content and optional files.
    - For retrieval, it lists all active stories.

    For creating a new story, use HTTP POST method with 'content' and optional 'files' in the request body.
    """

    # region Retrieve and create stories
    def get_serializer_class(self):
        if self.action == 'create':
            return StoryCreateUpdateSerializer
        return StorySerializer

    def list(self, request, *args, **kwargs):
        following_users = request.user.following.all()
        following_stories = Story.actives.filter(author__in=following_users)
        serializer = self.get_serializer(following_stories, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        if request.data.get('content') is None:
            return Response('The caption must not be empty', status=status.HTTP_400_BAD_REQUEST)
        if request.data.get('files') is None:
            return Response('There must be at least one file', status=status.HTTP_400_BAD_REQUEST)
        content = request.data.get('content', '')
        files_data = request.data.getlist('files', [])
        data = {'content': content, 'files': files_data}
        serializer = self.get_serializer(data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'success': True, 'detail': "story created successfully"}, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        return Response({'detail': 'Method not allowed.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    # endregion


class PostStoryInteractionBaseView(APIView):
    """
    Base API view for handling interactions (like, comment) on posts and stories.
    """

    # region Helper methods
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
    # endregion


class LikeApiView(PostStoryInteractionBaseView):
    """
    API view for handling likes and dislikes on posts and stories.
    """

    # region Like or dislike
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

        return Response(data, status=status.HTTP_200_OK)
    # endregion


class CommentsApiView(PostStoryInteractionBaseView):
    """
    API view for handling comments on posts and stories.
    """

    # region Retrieve and create comments
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
        if 'body' not in request.data:
            return Response({'error': 'body is required'}, status=status.HTTP_400_BAD_REQUEST)
        # Get the object based on 'post_or_story' and 'pk'
        object = self._validate_post_or_story(post_or_story, pk)

        # Get ContentType for the object
        content_type = self._get_content_type(object)

        # Create a new comment
        data = {
            'replies': request.data.get('replies') if 'replies' in request.data else None,
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
    # endregion


class SearchApiView(APIView):
    def get(self, request, *args, **kwargs):
        if 'query' not in request.GET:
            return Response({"error": 'There must be a query'}, status=status.HTTP_400_BAD_REQUEST)

        if 'type' not in request.GET:
            return Response({"error": 'There must be a type'}, status=status.HTTP_400_BAD_REQUEST)

        query = request.GET.get('query')

        if request.GET.get('type') == "user":
            result = UserSerializer(User.search(query), many=True, context={'request': request}).data
        elif request.GET.get('type') == "post":
            result = PostSerializer(Post.search(query), many=True, context={'request': request}).data
        else:
            return Response({'error': 'type must be post or user'}, status=status.HTTP_400_BAD_REQUEST)

        data = {
            'query': query,
            'result': result
        }
        return Response(data, status=status.HTTP_200_OK)


class PopularTagsAPIView(APIView):
    """
    A view to retrieve the most popular tags based on their usage in posts.

    - It retrieves the most popular tags by counting the number of posts associated with each tag.
    - The top 10 most popular tags are returned.
    """

    def get(self, request, format=None):
        """
        Retrieves the most popular tags and returns them in descending order of their usage.

        Parameters:
        - request: The request object sent by the client.
        - format: The requested format of the response (e.g., JSON).

        Returns:
        - Response containing the top 10 most popular tags along with the number of posts associated with each tag.
        """
        popular_tags = Tag.objects.annotate(num_posts=Count('taggit_taggeditem_items')).order_by('-num_posts')[:10]

        serialized_tags = [{'name': tag.name, 'num_posts': tag.num_posts} for tag in popular_tags]
        return Response(serialized_tags)


class SavedPostsListApiView(APIView):
    def get(self, request, *args, **kwargs):
        user_saved_posts = request.user.saved_posts.all()
        print(user_saved_posts)
        serializer = PostSerializer(user_saved_posts, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class SavedPostsApiView(APIView):

    def post(self, request, post_id):
        try:
            post = Post.actives.get(id=post_id)
        except Post.DoesNotExist:
            return Response({'error': 'Post Not Found!'}, status=status.HTTP_404_NOT_FOUND)
        if request.user in post.saved.all():
            post.saved.remove(request.user)
            return Response({'message': "Post has not been saved!", 'is_saved': False}, status=status.HTTP_200_OK)
        else:
            post.saved.add(request.user)
            return Response({'message': "Post has been saved!", 'is_saved': True}, status=status.HTTP_200_OK)

