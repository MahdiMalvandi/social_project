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

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


class PostsApiViewSet(ModelViewSet):
    """
    This view set handles the retrieval, creation, updating, and deletion of posts.

    For creation, it accepts a POST request with a caption and optional files.
    For retrieval, it lists all active posts.

    For creating a new post, use HTTP POST method with 'caption' and optional 'files' in the request body.
    For updating a post, use HTTP PUT method with the updated 'caption' and 'files' in the request body.
    For deleting a post, use HTTP DELETE method.

    When deleting a post, only the author of the post can delete it.

    """
    queryset = Post.actives.all()
    serializer_class = PostSerializer
    pagination_class = PageNumberPagination

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update':
            return PostCreateUpdateSerializer
        return PostSerializer

    def get_queryset(self):
        """
        This method returns the queryset of posts.
        """
        all_posts = Post.actives.all()
        user = self.request.user
        following_posts = Post.actives.filter(author__in=user.following.all())
        queryset = following_posts | all_posts
        return queryset

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['caption'],
            properties={
                'caption': openapi.Schema(type=openapi.TYPE_STRING, description='Caption for the post'),
                'files': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_FILE),
                                        description='List of files (optional)'),
            },
        ),
        responses={
            201: openapi.Response('Post created successfully'),
            400: 'Invalid request body',
        }
    )
    def create(self, request, *args, **kwargs):
        """
        Create a new post.
        """
        caption = request.data.get('caption', '')
        files_data = request.data.getlist('files', [])

        data = {'caption': caption, 'files': files_data}
        serializer = self.get_serializer(data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'success': True, 'detail': "Post created successfully"}, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['caption'],
            properties={
                'caption': openapi.Schema(type=openapi.TYPE_STRING, description='Updated caption for the post'),
                'files': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_FILE),
                                        description='Updated list of files (optional)'),
            },
        ),
        responses={
            200: openapi.Response('Post updated successfully'),
            400: 'Invalid request body',
            404: 'Post not found',
        }
    )
    def update(self, request, *args, **kwargs):
        """
        Update an existing post.
        """
        try:
            post = Post.objects.get(pk=kwargs['pk'])
        except Post.DoesNotExist:
            return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)

        caption = request.data.get('caption', '')
        files_data = request.data.getlist('files', [])

        data = {'caption': caption, 'files': files_data}
        serializer = self.get_serializer(instance=post, data=data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'success': True, 'detail': "Post updated successfully"}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        responses={
            200: openapi.Response('Post deleted successfully'),
            400: 'Invalid request',
            404: 'Post not found',
            403: 'Forbidden: You cannot delete other user\'s posts',
        }
    )
    def destroy(self, request, *args, **kwargs):
        """
        Delete an existing post.
        """
        try:
            post = Post.objects.get(pk=kwargs['pk'])
        except Post.DoesNotExist:
            return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)

        if post.author != request.user:
            return Response({'error': "You cannot delete other user's posts"}, status=status.HTTP_403_FORBIDDEN)

        post.delete()
        return Response({'success': True, 'detail': "Post deleted successfully"}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        responses={
            200: openapi.Response('Retrieved post details'),
            404: 'Post not found',
        }
    )
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve details of a specific post.
        """
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        responses={
            200: openapi.Response('List of all posts'),
        }
    )
    def list(self, request, *args, **kwargs):
        """
        List all posts.
        """
        return super().list(request, *args, **kwargs)


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

    def get_queryset(self):
        """
        This method returns the queryset of posts.
        """
        queryset = Story.public.filter(author__in=self.request.user.following_users.all())
        return queryset
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['content'],
            properties={
                'content': openapi.Schema(type=openapi.TYPE_STRING, description='Content of the story'),
                'files': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_FILE),
                                        description='List of files (optional)'),
            },
        ),
        responses={
            201: openapi.Response('Story created successfully'),
            400: 'Invalid request body',
        }
    )
    def create(self, request, *args, **kwargs):
        """
        Create a new story.
        """
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
        return Response({'success': True, 'detail': "Story created successfully"}, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        responses={
            405: 'Method not allowed',
        }
    )
    def update(self, request, *args, **kwargs):
        """
        Update method is not allowed.
        """
        return Response({'detail': 'Method not allowed.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve details of a specific story.
        """
        return super().retrieve(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
        List all stories.
        """
        return super().list(request, *args, **kwargs)


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

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'post_or_story': openapi.Schema(type=openapi.TYPE_STRING, enum=['post', 'story'],
                                                description='Type of object to like/dislike'),
                'pk': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the post or story to like/dislike'),
            },
            required=['post_or_story', 'pk']
        ),
        responses={
            200: openapi.Response(description='Success', schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'likes_count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total likes count'),
                    'detail': openapi.Schema(type=openapi.TYPE_STRING, description='Details of the operation'),
                    'is_liked': openapi.Schema(type=openapi.TYPE_BOOLEAN,
                                               description='Indicates whether the user liked or disliked the post/story')
                }
            )),
            400: openapi.Response(description='Bad Request', schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                }
            )),
            404: openapi.Response(description='Not Found', schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                }
            ))
        }
    )
    def post(self, request, post_or_story, pk):
        """
        Handles liking/disliking posts or stories.

        To like or dislike a post or story, send a POST request to this endpoint
        with 'post_or_story' parameter set to either 'post' or 'story' and the
        'pk' parameter set to the ID of the post or story.

        Responses:
        - 200 OK: Returns the updated likes count and whether the user liked or disliked the post/story.
        - 400 Bad Request: If the 'post_or_story' parameter is neither 'post' nor 'story'.
        - 404 Not Found: If the post or story with the specified ID does not exist.
        """

        user = request.user

        if post_or_story not in ['post', 'story']:
            return Response({'error': '"post_or_story" should be either a "post" or a "story"'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            object = self._validate_post_or_story(post_or_story, pk)
        except:
            return Response({'error': 'Object not found'}, status=status.HTTP_404_NOT_FOUND)

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

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('post_or_story', openapi.IN_PATH, type=openapi.TYPE_STRING, enum=['post', 'story'],
                              description='Type of object to retrieve comments for'),
            openapi.Parameter('pk', openapi.IN_PATH, type=openapi.TYPE_INTEGER,
                              description='ID of the post or story to retrieve comments for'),
        ],
        responses={
            200: openapi.Response(description='Success', schema=openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                    'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Comment ID'),
                    'body': openapi.Schema(type=openapi.TYPE_STRING, description='Comment body'),
                    'user': openapi.Schema(type=openapi.TYPE_STRING, description='Username of the commenter'),
                    'created_at': openapi.Schema(type=openapi.TYPE_STRING, description='Comment creation date'),
                    'replies': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(
                        type=openapi.TYPE_OBJECT, properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Reply ID'),
                            'body': openapi.Schema(type=openapi.TYPE_STRING, description='Reply body'),
                            'user': openapi.Schema(type=openapi.TYPE_STRING, description='Username of the replier'),
                            'created_at': openapi.Schema(type=openapi.TYPE_STRING, description='Reply creation date'),
                        }
                    ), description='List of replies to the comment')
                })
            )),
            400: openapi.Response(description='Bad Request', schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                }
            )),
            404: openapi.Response(description='Not Found', schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                }
            ))
        }
    )
    def get(self, request, post_or_story, pk):
        """
        Retrieve comments for a post or story.

        To retrieve comments for a post or story, send a GET request to this endpoint
        with 'post_or_story' parameter set to either 'post' or 'story' and the
        'pk' parameter set to the ID of the post or story.

        Responses:
        - 200 OK: Returns a list of comments for the specified post/story.
        - 400 Bad Request: If the 'post_or_story' parameter is neither 'post' nor 'story'.
        - 404 Not Found: If the post or story with the specified ID does not exist.
        """

        user = request.user

        if post_or_story not in ['post', 'story']:
            return Response({'error': '"post_or_story" should be either a "post" or a "story"'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            object = self._validate_post_or_story(post_or_story, pk)
        except:
            return Response({'error': 'Object not found'}, status=status.HTTP_404_NOT_FOUND)

        content_type = self._get_content_type(object)

        comments = Comment.objects.filter(content_type=content_type, object_id=object.id, replies=None)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('post_or_story', openapi.IN_PATH, type=openapi.TYPE_STRING, enum=['post', 'story'],
                              description='Type of object to create a comment for'),
            openapi.Parameter('pk', openapi.IN_PATH, type=openapi.TYPE_INTEGER,
                              description='ID of the post or story to create a comment for'),
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['body'],
            properties={
                'body': openapi.Schema(type=openapi.TYPE_STRING, description='Body of the comment'),
                'replies': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_INTEGER),
                                          description='List of reply IDs (optional)')
            }
        ),
        responses={
            201: openapi.Response(description='Success', schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message'),
                    'comments': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(
                        type=openapi.TYPE_OBJECT, properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Comment ID'),
                            'body': openapi.Schema(type=openapi.TYPE_STRING, description='Comment body'),
                            'user': openapi.Schema(type=openapi.TYPE_STRING, description='Username of the commenter'),
                            'created_at': openapi.Schema(type=openapi.TYPE_STRING, description='Comment creation date'),
                            'replies': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(
                                type=openapi.TYPE_OBJECT, properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Reply ID'),
                                    'body': openapi.Schema(type=openapi.TYPE_STRING, description='Reply body'),
                                    'user': openapi.Schema(type=openapi.TYPE_STRING,
                                                           description='Username of the replier'),
                                    'created_at': openapi.Schema(type=openapi.TYPE_STRING,
                                                                 description='Reply creation date'),
                                }
                            ), description='List of replies to the comment')
                        }
                    ), description='List of all comments after creation')
                }
            )),
            400: openapi.Response(description='Bad Request', schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                }
            )),
            404: openapi.Response(description='Not Found', schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                }
            ))
        }
    )
    def post(self, request, post_or_story, pk):
        """
        Create a new comment on a post or story.

        To create a new comment on a post or story, send a POST request to this endpoint
        with 'post_or_story' parameter set to either 'post' or 'story' and the
        'pk' parameter set to the ID of the post or story.

        Responses:
        - 201 Created: Returns a list of all comments after successful creation of the new comment.
        - 400 Bad Request: If the 'post_or_story' parameter is neither 'post' nor 'story' or the 'body' parameter is missing.
        - 404 Not Found: If the post or story with the specified ID does not exist.
        """

        user = request.user

        if post_or_story not in ['post', 'story']:
            return Response({'error': '"post_or_story" should be either a "post" or a "story"'},
                            status=status.HTTP_400_BAD_REQUEST)
        if 'body' not in request.data:
            return Response({'error': 'body is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            object = self._validate_post_or_story(post_or_story, pk)
        except:
            return Response({'error': 'Object not found'}, status=status.HTTP_404_NOT_FOUND)

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

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('query', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Search query string',
                              required=True),
            openapi.Parameter('type', openapi.IN_QUERY, type=openapi.TYPE_STRING, enum=['user', 'post'],
                              description='Type of search (user or post)', required=True),
        ],
        responses={
            200: openapi.Response(description='Success', schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'query': openapi.Schema(type=openapi.TYPE_STRING, description='Search query string'),
                    'result': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(
                        type=openapi.TYPE_OBJECT, description='Search result', properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the user or post'),
                            'username': openapi.Schema(type=openapi.TYPE_STRING,
                                                       description='Username of the user or title of the post'),
                            'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email of the user'),
                            'created_at': openapi.Schema(type=openapi.TYPE_STRING,
                                                         description='Creation date of the user or post'),
                            'content': openapi.Schema(type=openapi.TYPE_STRING,
                                                      description='Content of the post (only applicable for type=post)'),
                        }
                    ))
                }
            )),
            400: openapi.Response(description='Bad Request', schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                }
            ))
        }
    )
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

    def get(self, request):
        """
        Retrieve the most popular tags.

        Retrieves the most popular tags based on their usage in posts.
        The result includes the name of each tag and the number of posts associated with it.

        Responses:
        - 200 OK: Returns a list of the most popular tags.
        """

        popular_tags = Tag.objects.annotate(num_posts=Count('taggit_taggeditem_items')).order_by('-num_posts')[:10]

        serialized_tags = [{'name': tag.name, 'num_posts': tag.num_posts} for tag in popular_tags]
        return Response(serialized_tags, status=status.HTTP_200_OK)


class SavedPostsListApiView(APIView):
    """
    Retrieve the saved posts for the current user.

    Responses:
    - 200 OK: Returns a list of saved posts for the current user.
    """

    def get(self, request, *args, **kwargs):
        serializer = PostSerializer(request.user.saved_posts.all(), many=True, context={'request': request})
        return Response(serializer.data)


class SavedPostsApiView(APIView):
    """
    Save or unsave a post for the current user.

    Responses:
    - 404 Not Found: If the specified post does not exist.
    - 200 OK: If the post has been successfully saved or unsaved.
    """

    def post(self, request, post_id):
        try:
            post = Post.actives.get(id=post_id)
        except Post.DoesNotExist:
            return Response({'error': 'Post Not Found!'}, status=status.HTTP_404_NOT_FOUND)

        action = post.saved.remove if request.user in post.saved.all() else post.saved.add
        action(request.user)

        return Response({'message': "Post has {}been saved!".format("" if request.user in post.saved.all() else "not "),
                         'is_saved': request.user in post.saved.all()})


class GetPostsByTagApiView(APIView):
    @swagger_auto_schema(
        operation_description="Retrieve posts by tag name",
        manual_parameters=[
            openapi.Parameter(
                name="tag_name",
                in_=openapi.IN_PATH,
                type=openapi.TYPE_STRING,
                description="Name of the tag to search for",
                required=True,
            )
        ],
        responses={
            200: "Returns a list of posts with the specified tag name",
            404: "Tag not found",
        },
    )
    def get(self, request, tag_name, *args, **kwargs):
        """
        Retrieve posts by tag name.

        Retrieves posts associated with the specified tag name.

        :param tag_name: Name of the tag to search for.
        :type tag_name: str

        :return: A list of posts with the specified tag name.
        :rtype: Response
        """
        serializer = PostSerializer(Post.actives.filter(tags__name=tag_name), many=True, context={"request": request})
        return Response({'tag': tag_name, 'posts': serializer.data})
