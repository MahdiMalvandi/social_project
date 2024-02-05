from django.http import HttpResponseForbidden
from rest_framework import status
from rest_framework.response import Response


class AdminPermissionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/admin/"):
            print(request)
            return Response("You Are Not Admin", status=status.HTTP_403_FORBIDDEN)

        response = self.get_response(request)
        return response
