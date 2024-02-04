# your_project/celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')

# Create a Celery instance and configure it using the settings module.
app = Celery('your_project')

# Load task modules from all registered Django app configs.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodiscover tasks in all installed apps.
app.autodiscover_tasks()
