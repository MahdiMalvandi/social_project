# models.py

from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from users.models import User
from taggit.managers import TaggableManager


class Post(models.Model):
    caption = models.TextField(max_length=10000)
    tags = TaggableManager(blank=True)
    author = models.ForeignKey(User, related_name='posts', on_delete=models.SET_NULL, null=True)
    comments = GenericRelation('Comment', null=True, blank=True)
    files = GenericRelation('FileMedia')
    likes = GenericRelation("Like", null=True, blank=True)


class Story(models.Model):
    content = models.TextField(max_length=10000)
    likes = GenericRelation("Like")
    author = models.ForeignKey(User, related_name='stories', on_delete=models.CASCADE)
    comments = GenericRelation("Comment", null=True, blank=True)
    files = GenericRelation("FileMedia")

    def __str__(self):
        return f"Story by {self.author.username}"


class Like(models.Model):
    user = models.ForeignKey(User, related_name='likes', on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.content_object}"


class Comment(models.Model):
    author = models.ForeignKey(User, related_name='comments', on_delete=models.CASCADE)
    body = models.TextField(max_length=1000)
    replies = models.ForeignKey('self', on_delete=models.CASCADE, related_name='comment_replies', null=True, blank=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return f"{self.author.username} - {self.body[:20]}..."


class FileMedia(models.Model):
    file = models.FileField(upload_to='files/')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file.name} - {self.content_object}"
