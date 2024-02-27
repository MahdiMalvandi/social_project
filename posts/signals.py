from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import Post, Comment, Story, Like
from notification.tools import add_notification_object


# for like post and story
@receiver(post_save, sender=Like)
def send_notification_for_like(sender, instance, created, **kwargs):
    if created:
        notif_message = f'User {instance.user.get_full_name()} with the username {instance.user.username} liked your ' \
                        f'{instance.content_type.model}. {instance.content_type.model} : ' \
                        f'{instance.content_object.caption[0:20]} ' \
                        f'{"..." if len(instance.content_object.caption) > 20 else ""}'
        user_post = instance.content_object.author
        add_notification_object(user_post, notif_message)


# for add a comment
@receiver(post_save, sender=Comment)
def add_notification_for_comments(sender, instance, created, **kwargs):
    if created:
        notif_message = f'User {instance.author} with the username {instance.author} left a comment for your' \
                        f' {instance.content_type.model}' \
                        f'. Comment text:' \
                        f' {instance.body[0:20]} ' \
                        f'{"..." if len(instance.body) > 20 else ""}'
        user_post = instance.content_object.author
        add_notification_object(user_post, notif_message)


@receiver(post_save, sender=Post)
def add_notification_for_followers_when_post_was_made(sender, instance, created, **kwargs):
    if created:
        notif_message = f"User {instance.author.get_full_name()} posted a post with the username " \
                        f"{instance.author.username}. Post caption:{instance.caption[0:20]}" \
                        f" {'...' if len(instance.caption) > 20 else ''}"

        followers = instance.author.followers_relations.all()
        for follower in followers:
            add_notification_object(follower.follower, notif_message)


@receiver(post_save, sender=Story)
def add_notification_for_followers_when_story_was_made(sender, instance, created, **kwargs):
    if created:
        notif_message = f"User {instance.author.get_full_name()} posted a story with the username " \
                        f"{instance.author.username}. Story content:{instance.caption[0:20]}" \
                        f" {'...' if len(instance.caption) > 20 else ''}"

        followers = instance.author.followers_relations.all()
        for follower in followers:
            add_notification_object(follower.follower, notif_message)
