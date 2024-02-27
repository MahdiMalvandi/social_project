from django.db.models.signals import post_save, post_delete
from .models import User, Follow
from notification.models import Notification
from django.dispatch import receiver
from notification.tools import add_notification_object


@receiver(post_save, sender=Follow)
def add_notification_for_follow(sender, instance, created, **kwargs):
    if created:
        notif_message = f'User {instance.follower.get_full_name()} followed you with @{instance.follower.username} ID'
        add_notification_object(instance.following, notif_message)


@receiver(post_delete, sender=Follow)
def add_notification_for_unfollow(sender, instance, **kwargs):
    notif_message = f'User {instance.follower.get_full_name()} unfollowed you with @{instance.follower.username} ID'
    add_notification_object(instance.following, notif_message)
