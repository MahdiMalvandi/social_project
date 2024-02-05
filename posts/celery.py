import os

from celery import Celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'social_project.settings')

app = Celery('social_project_celery')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

print('---------------------------- start ------------------------------------')
