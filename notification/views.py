from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from .models import Notification


class SeenNotificationApiView(APIView):
    def post(self, request, pk, *args, **kwargs):
        try:
            notification = Notification.objects.get(pk=pk)
        except Notification.DoesNotExist:
            return Response({'error': 'Notification Not Found'}, status=status.HTTP_404_NOT_FOUND)
        notification.is_seen = True
        notification.save()
        return Response({'success': True, 'message': 'notification has been seen'})

