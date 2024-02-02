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
    file = serializers.FileField(max_length=10000)

    class Meta:
        model = FileMedia
        fields = ('id', 'file', 'uploaded_at')

    def create(self, validated_data):
        return self


# endregion

# region post serializer
class PostSerializer(serializers.ModelSerializer):
    author = UserDetailSerializer()
    likes_count = serializers.SerializerMethodField()
    files = FileMediaSerializer(read_only=True, many=True)
    comments_count = serializers.SerializerMethodField(read_only=True)
    is_liked = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Post
        fields = ('id', 'caption', 'files', 'is_liked', 'author', 'comments_count', 'likes_count')

    # method fields
    def get_is_liked(self, obj):
        try:
            like = Like.objects.get(user=self.context['request'].user, content_type__model='post', object_id=obj.id)
            return True
        except Like.DoesNotExist:
            return False

    def get_comments_count(self, obj):
        comment_count = obj.comments.count()
        return comment_count

    def get_likes_count(self, obj):
        likes_count = obj.likes.count()
        return likes_count

    def get_files(self, obj):
        files_data = FileMediaSerializer(obj.files.all(), many=True, context={'request': self.context['request']}).data
        return files_data


class PostCreateUpdateSerializer(serializers.Serializer):
    caption = serializers.CharField(max_length=1000)
    author = UserSerializer(read_only=True)
    files = serializers.ListField(child=serializers.FileField())

    def create(self, validated_data):
        files_data = validated_data['files']

        post = Post.actives.create(caption=validated_data['caption'], author=self.context['request'].user)

        for file in files_data:
            print(file)
            file_obj = FileMedia.objects.create(
                file=file,
                content_type=ContentType.objects.get_for_model(Post),
                object_id=post.id
            )
            file_obj.save()

        post.save()

        return post


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
