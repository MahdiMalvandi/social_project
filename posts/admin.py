# admin.py

from django.contrib import admin
from .models import *


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ['content', 'author', 'get_likes']

    def get_likes(self, obj):
        likes = obj.likes.all()
        return ", ".join([like.user.username for like in likes])

    get_likes.short_description = 'Likes'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'body', 'replies', 'content_type']


@admin.register(FileMedia)
class FileMediaAdmin(admin.ModelAdmin):
    list_display = ['file', 'content_type', 'object_id', 'content_object']


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['caption', 'author', 'get_likes', 'get_tags']

    def get_likes(self, obj):
        likes = obj.likes.all()
        return ", ".join([like.user.username for like in likes])

    get_likes.short_description = 'Likes'

    def get_tags(self, obj):
        tags = obj.tags.all()
        return ", ".join([tag.name for tag in tags])

    get_tags.short_description = 'Tags'
