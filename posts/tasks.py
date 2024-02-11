from celery import shared_task
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from .models import Story, FileMedia, Post
from time import sleep
from celery import shared_task
from .celery import app


@shared_task
def deactivate_stories():
    active_stories = Story.actives.filter(created__lt=timezone.now() - timezone.timedelta(hours=1))
    for story in active_stories:
        story.is_active = False
        story.save()


# @app.task
# def upload_files(file_paths, post_id):
#     for file_path in file_paths:
#         sleep(3)
#         with open(file_path, 'rb') as file_data:
#             file_obj = FileMedia.objects.create(
#                 file=file_data,
#                 content_type=ContentType.objects.get_for_model(Post),
#                 object_id=post_id
#             )
#             file_obj.save()
#             print(f'file: {file_obj} uploaded')
#     return {"status": True}
