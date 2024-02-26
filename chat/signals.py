from .models import Conversation, Message
from django.dispatch import receiver
from django.db.models.signals import post_save
from notification.models import Notification

@receiver(post_save, sender=Message)
def add_notification_for_create_message(sender, instance, created, **kwargs):
    if created:
        conversation = instance.conversation
        user = instance.sender
        second_user = conversation.initiator if user == conversation.receiver else conversation.receiver
        notif_message = f'{user.get_full_name()} : {instance.text[0:50]} {"..." if len(instance.text) > 50 else ""}'
        notif_obj = Notification.objects.create(
            user=second_user,
            message=notif_message
        )
        notif_obj.save()