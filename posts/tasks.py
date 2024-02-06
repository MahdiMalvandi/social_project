from celery import shared_task
from django.utils import timezone
from .models import Post

@shared_task
def deactivate_stories():
    print('task run')
    active_stories = Post.actives.filter(created__lte=timezone.now() - timezone.timedelta(seconds=10))
    for story in active_stories:
        story.is_active = False
        story.save()
