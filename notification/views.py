from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from .models import Notification
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


class SeenNotificationApiView(APIView):
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'notification_id': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, description="the id of the notification"),
            },
            required=['email'],
            description="Email address of the user who forgot their password."
        ),
        responses={
            200: "Email sent successfully. Please proceed to the `reset-password/confirm/` endpoint with the provided code.",
            404: "notification not found."
        }
    )
    def post(self, request, pk, *args, **kwargs):
        try:
            notification = Notification.objects.get(pk=pk)
        except Notification.DoesNotExist:
            return Response({'error': 'Notification Not Found'}, status=status.HTTP_404_NOT_FOUND)
        notification.is_seen = True
        notification.save()
        return Response({'success': True, 'message': 'notification has been seen'})

