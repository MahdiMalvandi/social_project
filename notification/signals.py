from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .serializers import NotificationSerializer
from .models import Notification

@receiver(post_save, sender=Notification)
def notification_created(sender, instance, created, **kwargs):
    if created:
        channel_layer = get_channel_layer()
        serializer = NotificationSerializer(instance)
        async_to_sync(channel_layer.group_send)(
            f'notification_{instance.user.username}',
            {
                "type": "send_notification",
                "message": serializer.data
            }
        )
        print(f'notif sent to {instance.user.username}')
