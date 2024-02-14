from django.utils import timezone
from .models import Story, FileMedia, Post
from celery import shared_task


@shared_task
def deactivate_stories():
    active_stories = Story.actives.filter(created__lt=timezone.now() - timezone.timedelta(hours=1))
    for story in active_stories:
        story.is_active = False
        story.save()
