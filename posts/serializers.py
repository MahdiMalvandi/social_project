from rest_framework import serializers
from .models import *
from users.serializers import *


class LikeSerializer(serializers.ModelSerializer):
    author = UserDetailSerializer()

    class Meta:
        model = Like
        fields = '__all__'


class CommentSerializer(serializers.ModelSerializer):
    author = UserDetailSerializer()
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ('id', 'body', 'author', 'replies')

    def get_replies(self, obj):
        comment_replies_data = CommentSerializer(obj.comment_replies.all(), many=True).data
        return comment_replies_data


class FileMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileMedia
        fields = ('id', 'file', 'uploaded_at')


class PostSerializer(serializers.ModelSerializer):
    author = UserDetailSerializer()
    likes = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    files = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ('id', 'caption', 'comments', 'files', 'likes', 'author')

    def get_likes(self, obj):
        likes_data = LikeSerializer(obj.likes.all(), many=True).data
        return likes_data

    def get_comments(self, obj):
        comment_data = CommentSerializer(obj.comments.all(), many=True).data
        return comment_data

    def get_files(self, obj):
        files_data = FileMediaSerializer(obj.files.all(), many=True, context={'request': self.context['request']}).data
        return files_data
