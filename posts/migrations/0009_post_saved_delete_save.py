# Generated by Django 5.0.1 on 2024-02-23 10:52

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0008_save'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='saved',
            field=models.ManyToManyField(related_name='saved_posts', to=settings.AUTH_USER_MODEL),
        ),
        migrations.DeleteModel(
            name='Save',
        ),
    ]
