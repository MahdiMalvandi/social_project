from .models import Notification


def add_notification_object(user, message):
    notif_obj = Notification.objects.create(
        user=user,
        message=message
    )
    notif_obj.save()
