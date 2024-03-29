# Generated by Django 5.0.1 on 2024-01-23 11:33

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
import users.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Follow',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('first_name', models.CharField(max_length=30)),
                ('last_name', models.CharField(max_length=30)),
                ('username', models.CharField(max_length=32, unique=True)),
                ('email', models.EmailField(max_length=50, unique=True)),
                ('phone_number', models.BigIntegerField(unique=True, validators=[django.core.validators.RegexValidator('^989[0-3,9]\\d8$', 'Enter a valid mobile number')])),
                ('profile', models.ImageField(blank=True, null=True, upload_to=users.models.user_profile_upload_path)),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('last_seen', models.DateTimeField(null=True, verbose_name='last seen date')),
                ('gender', models.CharField(blank=True, choices=[('m', 'Male'), ('f', 'Female')], max_length=5, null=True)),
                ('date_of_birth', models.DateTimeField(blank=True, null=True)),
                ('bio', models.TextField(blank=True, null=True)),
                ('following', models.ManyToManyField(related_name='following_users', through='users.Follow', to='users.user')),
            ],
            options={
                'db_table': 'users',
            },
        ),
        migrations.CreateModel(
            name='OtpToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=6)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('expired', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='otp_tokens', to='users.user')),
            ],
        ),
        migrations.AddField(
            model_name='follow',
            name='follower',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='following_relations', to='users.user'),
        ),
        migrations.AddField(
            model_name='follow',
            name='following',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='followers_relations', to='users.user'),
        ),
        migrations.AlterUniqueTogether(
            name='follow',
            unique_together={('follower', 'following')},
        ),
    ]
