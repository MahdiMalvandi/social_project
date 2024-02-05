from celery import shared_task
from django.utils import timezone
from .models import Post

@shared_task
def deactivate_stories():
    print('task run')
    # پست‌های فعال با تایم ساخته شدن بیشتر از ۱۰ ثانیه پیش را پیدا کنید و به غیرفعال تغییر دهید
    active_stories = Post.actives.filter(created__lte=timezone.now() - timezone.timedelta(seconds=10))
    for story in active_stories:
        story.is_active = False
        story.save()
