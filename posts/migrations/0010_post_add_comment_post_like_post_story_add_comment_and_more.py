# Generated by Django 5.0.1 on 2024-03-02 13:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0009_post_saved_delete_save'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='add_comment',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='post',
            name='like_post',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='story',
            name='add_comment',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='story',
            name='like_post',
            field=models.BooleanField(default=True),
        ),
    ]
