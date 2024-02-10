from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline

from .models import *


class CommentInline(GenericTabularInline):
    model = Comment
    extra = 1


class FileMediaInline(GenericTabularInline):
    model = FileMedia
    extra = 1


class LikeInline(GenericTabularInline):
    model = Like
    extra = 1


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'content', 'author', 'get_likes', 'created']
    inlines = [
        CommentInline,
        LikeInline,
        FileMediaInline
    ]

    def get_likes(self, obj):
        likes = obj.likes.all()
        return ", ".join([like.user.username for like in likes])

    get_likes.short_description = 'Likes'


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['id', 'caption', 'author', 'get_likes', 'get_tags']
    inlines = [
        CommentInline,
        LikeInline,
        FileMediaInline
    ]

    def get_likes(self, obj):
        likes = obj.likes.all()
        return ", ".join([like.user.username for like in likes])

    get_likes.short_description = 'Likes'

    def get_tags(self, obj):
        tags = obj.tags.all()
        return ", ".join([tag.name for tag in tags])

    get_tags.short_description = 'Tags'
