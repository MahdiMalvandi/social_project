from rest_framework import serializers
from .models import *
from users.serializers import *


# region like serializer
class LikeSerializer(serializers.ModelSerializer):
    author = UserDetailSerializer()

    class Meta:
        model = Like
        fields = '__all__'


# endregion

# region comment serializer
class CommentSerializer(serializers.ModelSerializer):
    author = UserDetailSerializer()
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ('id', 'body', 'author', 'replies')

    def get_replies(self, obj):
        comment_replies_data = CommentSerializer(obj.comment_replies.all(), many=True).data
        return comment_replies_data


# endregion

# region file media serializer
class FileMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileMedia
        fields = ('id', 'file', 'uploaded_at')


# endregion

# region post serializer
class PostSerializer(serializers.ModelSerializer):
    author = UserDetailSerializer()
    likes = LikeSerializer(read_only=True, many=True)
    files = FileMediaSerializer(read_only=True, many=True)
    comments_count = serializers.SerializerMethodField(read_only=True)
    likes_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Post
        fields = ('id', 'caption', 'files', 'likes', 'author', 'comments_count', 'likes_count')


    # method fields
    def get_likes(self, obj):
        likes_data = LikeSerializer(obj.likes.all(), many=True).data
        return likes_data

    def get_comments_count(self, obj):
        comment_count = obj.comments.count()
        return comment_count

    def get_likes_count(self, obj):
        likes_count = obj.likes.count()
        return likes_count

    def get_files(self, obj):
        files_data = FileMediaSerializer(obj.files.all(), many=True, context={'request': self.context['request']}).data
        return files_data


# endregion

# region story serializer

class StorySerializer(serializers.ModelSerializer):
    author = UserDetailSerializer()
    likes = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    files = serializers.SerializerMethodField()

    class Meta:
        model = Story
        fields = ['content', 'author', 'likes', 'author', 'comments', 'files']

    def get_likes(self, obj):
        likes_data = LikeSerializer(obj.likes.all(), many=True).data
        return likes_data

    def get_comments(self, obj):
        comment_data = CommentSerializer(obj.comments.all(), many=True).data
        return comment_data

    def get_files(self, obj):
        files_data = FileMediaSerializer(obj.files.all(), many=True, context={'request': self.context['request']}).data
        return files_data
# endregion
