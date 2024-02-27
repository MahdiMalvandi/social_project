from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .serializers import NotificationSerializer
from .models import Notification


@receiver(post_save, sender=Notification)
def notification_created(sender, instance, created, **kwargs):
    """
    Sends a notification through WebSocket when a new notification is created.

    Parameters:
        sender (class): The sender class of the signal.
        instance (Notification): The instance of the Notification model.
        created (bool): Indicates whether the instance was created.
        **kwargs: Additional keyword arguments.
    """
    if created:
        # Get the channel layer
        channel_layer = get_channel_layer()

        # Serialize the notification
        serializer = NotificationSerializer(instance)

        # Send the notification to the corresponding user's group
        async_to_sync(channel_layer.group_send)(
            f'notification_{instance.user.username}',
            {
                "type": "send_notification",
                "message": serializer.data
            }
        )

        # Print debug message
        print(f'Notification sent to {instance.user.username}')
