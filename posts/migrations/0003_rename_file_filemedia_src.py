# Generated by Django 5.0.1 on 2024-02-01 16:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0002_alter_post_managers_post_is_active'),
    ]

    operations = [
        migrations.RenameField(
            model_name='filemedia',
            old_name='file',
            new_name='src',
        ),
    ]
