from django.contrib import admin
from .models import *


class CommentTabularInline(admin.TabularInline):
    model = Comment
    extra = 0


class FileMediaTabularInline(admin.TabularInline):
    model = FileMedia
    extra = 0


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['caption', 'author', 'get_likes', 'get_tags']
    inlines = [
        CommentTabularInline,
        FileMediaTabularInline
    ]

    def get_likes(self, obj):
        likes = obj.likes.all()
        return ", ".join([like.user.username for like in likes])

    get_likes.short_description = 'Likes'

    def get_tags(self, obj):
        tags = obj.tags.all()
        return ", ".join([tag.name for tag in tags])

    get_tags.short_description = 'Tags'
