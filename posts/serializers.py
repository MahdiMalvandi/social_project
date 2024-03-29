from rest_framework import serializers
from .models import *
from users.serializers import UserSerializer
from taggit.serializers import (TagListSerializerField,
                                TaggitSerializer)

# region Like Serializer
class LikeSerializer(serializers.ModelSerializer):
    """
    Serializer for handling Like model.

    Fields:
    - `author`: Serializes the author of the like using UserSerializer.
    """
    author = UserSerializer()

    class Meta:
        model = Like
        fields = '__all__'

# endregion

# region Comment Serializer
class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for handling Comment model.

    Fields:
    - `author`: Serializes the author of the comment using UserSerializer.
    - `replies`: Serializes the replies of the comment using CommentSerializer.
    """
    author = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField(read_only=True)
    body = serializers.CharField()

    class Meta:
        model = Comment
        fields = ('id', 'body', 'author', 'replies')

    def get_replies(self, obj):
        """
        Method to serialize the replies of a comment.
        """
        comment_replies_data = self.__class__(obj.comment_replies.all(), many=True, context=self.context).data
        return comment_replies_data

class CommentCreateUpdateSerializer(serializers.Serializer):
    body = serializers.CharField(max_length=100000, min_length=3)
    replies = serializers.CharField(max_length=10000000, allow_null=True)
    object_id = serializers.CharField(max_length=1000000)
    content_type = serializers.PrimaryKeyRelatedField(queryset=ContentType.objects.all())



    def create(self, validated_data):
        """
        Create a new comment.

        Parameters:
        - `validated_data`: A dictionary of validated data.

        Returns:
        - A Comment object.
        """
        user = self.context['request'].user
        content_type = validated_data['content_type']
        object_id = validated_data['object_id']

        replies_data = validated_data.get('replies')
        if replies_data:
            try:
                replies = Comment.objects.get(pk=replies_data)
            except Comment.DoesNotExist:
                return serializers.ValidationError('The id of the comment on which the reply was posted is wrong')

        comment = Comment.objects.create(
            author=user,
            content_type=content_type,
            object_id=object_id,
            body=validated_data['body'],
            replies=replies if replies_data is not None else None
        )

        return comment

    def validate_body(self, value):
        bad_words = ['fuck', 'احمق']  # and other bad words
        for word in bad_words:
            value = value.replace(word, '*' * len(word))
        return value


# endregion

# region File Media Serializer
class FileMediaSerializer(serializers.ModelSerializer):
    """
    Serializer for handling FileMedia model.

    Fields:
    - `file`: Serializes the file of the media using a FileField.
    """
    file = serializers.FileField(max_length=10000)

    class Meta:
        model = FileMedia
        fields = ('id', 'file', 'uploaded_at')


# endregion

# region Post Serializer
class PostSerializer(TaggitSerializer, serializers.ModelSerializer):
    """
    Serializer for handling Post model.

    Fields:
    - `author`: Serializes the author of the post using UserSerializer.
    - `likes_count`: Serializes the count of likes on the post.
    - `files`: Serializes the files attached to the post using FileMediaSerializer.
    - `comments_count`: Serializes the count of comments on the post.
    - `is_liked`: Serializes whether the current user has liked the post.
    """
    author = UserSerializer()
    likes_count = serializers.SerializerMethodField()
    files = FileMediaSerializer(read_only=True, many=True)
    comments_count = serializers.SerializerMethodField(read_only=True)
    is_liked = serializers.SerializerMethodField(read_only=True)
    tags = TagListSerializerField()
    class Meta:
        model = Post
        fields = ('id', 'caption', 'files', 'is_liked', 'author', 'comments_count', 'likes_count', 'tags', 'can_add_comment',
                  'can_like'
                                                                                                           )

    # Method Fields
    def get_is_liked(self, obj):
        """
        Method to determine if the current user has liked the post.
        """
        try:
            Like.objects.get(user=self.context['request'].user, content_type__model='post', object_id=obj.id)
            return True
        except Like.DoesNotExist:
            return False

    def get_comments_count(self, obj):
        """
        Method to get the count of comments on the post.
        """
        return obj.comments.count()

    def get_likes_count(self, obj):
        """
        Method to get the count of likes on the post.
        """
        return obj.likes.count()

    def get_files(self, obj):
        """
        Method to serialize the files attached to the post.
        """
        return FileMediaSerializer(obj.files.all(), many=True, context={'request': self.context['request']}).data



class PostCreateUpdateSerializer(serializers.Serializer):
    """
    Serializer for creating and updating Post instances.

    Fields:
    - `caption`: Caption for the post.
    - `author`: Serialized user (read-only).
    - `files`: List of file attachments for the post.
    """
    caption = serializers.CharField(max_length=1000, required=False)
    author = UserSerializer(read_only=True)
    files = serializers.ListField(child=serializers.FileField(), required=False)
    can_add_comment = serializers.BooleanField(required=False, default=True)
    can_like = serializers.BooleanField(required=False, default=True)

    def create(self, validated_data):
        """
        Method to create a Post instance.
        """
        files_data = validated_data['files']
        can_add_comment = validated_data['can_add_comment']
        can_like = validated_data['can_like']
        post = Post.actives.create(
            caption=validated_data['caption'],
            author=self.context['request'].user,
            can_add_comment=can_add_comment,
            can_like=can_like
                                   )
        for file in files_data:
            file_obj = FileMedia.objects.create(
                file=file,
                content_type=ContentType.objects.get_for_model(Post),
                object_id=post.id,
            )
            file_obj.save()

        post.save()
        return post

    def update(self, instance, validated_data):
        files = validated_data['files'] if 'files' in validated_data else None
        if files:
            for file in files:
                file_obj = FileMedia.objects.create(
                    file=file,
                    content_type=ContentType.objects.get_for_model(Post),
                    object_id=instance.id,
                )
                file_obj.save()

        for key, value in validated_data.items():
            setattr(instance, key, value)

        instance.save()
        return instance

# endregion

# region Story Serializer
class StorySerializer(serializers.ModelSerializer):
    """
    Serializer for handling Story model.

    Fields:
    - `author`: Serializes the author of the story using UserSerializer.
    - `likes`: Serializes the likes on the story using LikeSerializer.
    - `comments`: Serializes the comments on the story using CommentSerializer.
    - `files`: Serializes the files attached to the story using FileMediaSerializer.
    """
    author = UserSerializer()
    is_liked = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    files = serializers.SerializerMethodField()

    class Meta:
        model = Story
        fields = ['id', 'content', 'author', 'is_liked', 'author', 'comments', 'files','can_add_comment',
                  'can_like']

    def get_is_liked(self, obj):
        """
        Method to determine if the current user has liked the post.
        """
        try:
            Like.objects.get(user=self.context['request'].user, content_type__model='post', object_id=obj.id)
            return True
        except Like.DoesNotExist:
            return False

    def get_comments(self, obj):
        """
        Method to serialize the comments on the story.
        """
        return CommentSerializer(obj.comments.all(), many=True).data

    def get_files(self, obj):
        """
        Method to serialize the files attached to the story.
        """
        return FileMediaSerializer(obj.files.all(), many=True, context={'request': self.context['request']}).data


class StoryCreateUpdateSerializer(serializers.Serializer):
    """
    Serializer for creating and updating Story instances.

    Fields:
    - `content`: Content of the story.
    - `author`: Serialized user (read-only).
    - `files`: List of file attachments for the story.
    """
    content = serializers.CharField(max_length=1000)
    author = UserSerializer(read_only=True)
    files = serializers.ListField(child=serializers.FileField())
    can_add_comment = serializers.BooleanField(required=False, default=True)
    can_like = serializers.BooleanField(required=False, default=True)

    def create(self, validated_data):
        """
        Method to create a Story instance.
        """
        files_data = validated_data['files']
        can_add_comment = validated_data['can_add_comment']
        can_like = validated_data['can_like']
        story = Story.actives.create(content=validated_data['content'], author=self.context['request'].user,can_add_comment=can_add_comment,
            can_like=can_like)

        for file in files_data:
            file_obj = FileMedia.objects.create(
                file=file,
                content_type=ContentType.objects.get_for_model(Story),
                object_id=story.id,

            )
            file_obj.save()

        story.save()
        return story

    def update(self, instance, validated_data):
        files = validated_data['files'] if 'files' in validated_data else None
        if files:
            for file in files:
                file_obj = FileMedia.objects.create(
                    file=file,
                    content_type=ContentType.objects.get_for_model(Story),
                    object_id=instance.id,
                )
                file_obj.save()

        for key, value in validated_data.items():
            setattr(instance, key, value)

        instance.save()
        return instance

# endregion
