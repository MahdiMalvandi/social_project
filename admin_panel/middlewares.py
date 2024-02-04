from django.http import HttpResponseForbidden


class AdminPermissionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.is_staff:
            return HttpResponseForbidden("You Are Not Admin")

        response = self.get_response(request)
        return response
