import re
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from taggit.models import Tag

from .models import Post, Story, Like, Comment, FileMedia
from .serializers import (PostSerializer, StorySerializer, PostCreateUpdateSerializer,
                          StoryCreateUpdateSerializer, CommentSerializer, CommentCreateUpdateSerializer,
                          UserSerializer)
from users.models import User


class PostsApiViewSet(ModelViewSet):
    """
    This view set handles the retrieval and creation of posts.

    For creation, it accepts a POST request with a caption and optional files.
    For retrieval, it lists all active posts.

    For creating a new post, use HTTP POST method with 'caption' and optional 'files' in the request body.
    """
    queryset = Post.actives.all()
    serializer_class = PostSerializer
    pagination_class = PageNumberPagination

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update':
            return PostCreateUpdateSerializer
        return PostSerializer

    def get_queryset(self):
        all_posts = Post.actives.all()
        user = self.request.user
        following_posts = Post.actives.filter(author__in=user.following.all())
        queryset = following_posts | all_posts
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

    def update(self, request, pk, *args, **kwargs):
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response({'error': 'Not Found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(data=request.data, instance=post)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'success': True, 'detail': "Post updated successfully"},
                        status=status.HTTP_200_OK)


class StoriesApiViewSet(ModelViewSet):
    """
    This view set handles the retrieval and creation of stories.

    For creation, it accepts a POST request with content and optional files.
    For retrieval, it lists all active stories.

    For creating a new story, use HTTP POST method with 'content' and optional 'files' in the request body.
    """
    queryset = Story.actives.all()
    serializer_class = StorySerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return StoryCreateUpdateSerializer
        return StorySerializer

    def create(self, request, *args, **kwargs):
        if request.data.get('content') is None:
            return Response('The content must not be empty', status=status.HTTP_400_BAD_REQUEST)
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


class PostStoryInteractionBaseView(APIView):
    """
    Base API view for handling interactions (like, comment) on posts and stories.
    """

    def _validate_post_or_story(self, post_or_story, pk):
        """
        Validate 'post_or_story' parameter and retrieve the object.
        """
        object_model = Story if post_or_story == 'story' else Post
        try:
            return object_model.actives.get(pk=pk)
        except object_model.DoesNotExist:
            raise NotFound("Object not found")

    def _get_content_type(self, object):
        """
        Get ContentType for the object.
        """
        return ContentType.objects.get_for_model(object)


class LikeApiView(PostStoryInteractionBaseView):
    """
    API view for handling likes and dislikes on posts and stories.
    """

    def post(self, request, post_or_story, pk):
        """
        Handles liking/disliking posts or stories.
        """

        user = request.user

        if post_or_story not in ['post', 'story']:
            return Response('"post_or_story" should be either a "post" or a "story"',
                            status=status.HTTP_400_BAD_REQUEST)

        object = self._validate_post_or_story(post_or_story, pk)

        content_type = self._get_content_type(object)

        like = Like.objects.filter(user=user, content_type=content_type, object_id=object.pk)
        if not object.can_like:
            return Response({'error': 'Like post is disabled'}, status=status.HTTP_400_BAD_REQUEST)
        if like.exists():
            like.delete()
            is_liked = False
        else:
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


class CommentsApiView(PostStoryInteractionBaseView):
    """
    API view for handling comments on posts and stories.
    """

    def get(self, request, post_or_story, pk):
        """
        Retrieve comments for a post or story.
        """

        user = request.user

        if post_or_story not in ['post', 'story']:
            return Response('"post_or_story" should be either a "post" or a "story"',
                            status=status.HTTP_400_BAD_REQUEST)

        object = self._validate_post_or_story(post_or_story, pk)

        content_type = self._get_content_type(object)

        comments = Comment.objects.filter(content_type=content_type, object_id=object.id, replies=None)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, post_or_story, pk):
        """
        Create a new comment on a post or story.
        """

        user = request.user

        if post_or_story not in ['post', 'story']:
            return Response('"post_or_story" should be either a "post" or a "story"',
                            status=status.HTTP_400_BAD_REQUEST)
        if 'body' not in request.data:
            return Response({'error': 'body is required'}, status=status.HTTP_400_BAD_REQUEST)

        object = self._validate_post_or_story(post_or_story, pk)

        if not object.can_add_comment:
            return Response({'error': 'Adding comments for this post is disabled'}, status=status.HTTP_400_BAD_REQUEST)
        content_type = self._get_content_type(object)

        data = {
            'replies': request.data.get('replies') if 'replies' in request.data else None,
            'content_type': content_type.pk,
            'object_id': object.id,
            'body': request.data['body']
        }
        serializer = CommentCreateUpdateSerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        response = {
            'message': 'success',
            'comments': CommentSerializer(object.comments.all(), many=True).data
        }
        return Response(response, status=status.HTTP_201_CREATED)


class SearchApiView(APIView):
    """
    A view to search for users or posts.
    """

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
    """

    def get(self, request, format=None):
        popular_tags = Tag.objects.annotate(num_posts=Count('taggit_taggeditem_items')).order_by('-num_posts')[:10]

        serialized_tags = [{'name': tag.name, 'num_posts': tag.num_posts} for tag in popular_tags]
        return Response(serialized_tags)


class SavedPostsListApiView(APIView):
    """
    A view to retrieve the saved posts for the current user.
    """

    def get(self, request, *args, **kwargs):
        user_saved_posts = request.user.saved_posts.all()
        serializer = PostSerializer(user_saved_posts, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class SavedPostsApiView(APIView):
    """
    A view to save or unsave a post for the current user.
    """

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


class GetPostsByTagApiView(APIView):
    def get(self, request, tag_name, *args, **kwargs):
        tag = Tag.objects.get(name=tag_name)
        posts = Post.actives.filter(tags=tag)

        serializer = PostSerializer(posts, many=True, context={"request": request})
        return Response({'tag': tag.name, 'posts': serializer.data})
