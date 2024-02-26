from django.db.models.signals import post_save, post_delete
from .models import User, Follow
from notification.models import Notification
from django.dispatch import receiver


@receiver(post_save, sender=Follow)
def add_notification_for_follow(sender, instance, created, **kwargs):
    if created:
        notif_message = f'User {instance.follower.get_full_name()} followed you with @{instance.follower.username} ID'
        notif_obj = Notification.objects.create(
            user=instance.following,
            message=notif_message
        )
        notif_obj.save()


@receiver(post_delete, sender=Follow)
def add_notification_for_follow(sender, instance, **kwargs):
    notif_message = f'User {instance.follower.get_full_name()} unfollowed you with @{instance.follower.username} ID'
    notif_obj = Notification.objects.create(
        user=instance.following,
         message=notif_message
    )
    notif_obj.save()
