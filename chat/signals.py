from notification.tools import add_notification_object
from .models import Conversation, Message
from django.dispatch import receiver
from django.db.models.signals import post_save
from notification.models import Notification


@receiver(post_save, sender=Message)
def add_notification_for_create_message(sender, instance, created, **kwargs):
    """
    Creates a notification when a new message is created.

    Parameters:
        sender (class): The sender class of the signal.
        instance (Message): The instance of the Message model.
        created (bool): Indicates whether the instance was created.
        **kwargs: Additional keyword arguments.
    """
    if created:
        # Determine the conversation and users involved
        conversation = instance.conversation
        user = instance.sender
        second_user = conversation.initiator if user == conversation.receiver else conversation.receiver

        # Create notification message
        notif_message = f'{user.get_full_name()} : {instance.text[0:50]} {"..." if len(instance.text) > 50 else ""}'

        # Create notification object
        add_notification_object(second_user, notif_message)

