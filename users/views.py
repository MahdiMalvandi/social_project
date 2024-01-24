import random
import string

from django.core.cache import cache
from django.core.mail import send_mail
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import User


# region login and registration
class LoginView(APIView):
    ...


class RegisterAndSendEmail(APIView):
    """
    Get User Data and Make an object and send verification email
    """

    def post(self, request, *args, **kwargs):
        data = request.data

        email = data['email']

        cached_code = cache.get(email)
        if cached_code:
            return Response({'error': 'Verification code already sent'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create(
            first_name=data['first_name'],
            last_name=data['last_name'],
            username=data['username'],
            email=data['email'],
            phone_number=data['phone_number'],
            profile=data['profile'] if 'profile' in data else None,
            gender=data['gender'],
            password=data['password']
        )

        verification_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

        # Send the verification code to the email

        title = "Account Verification"
        text = f"Hello," \
               f"Thank you for choosing our platform!" \
               f"To complete the account verification process, " \
               "Once you click the link, you will be prompted to enter the verification code provided below:" \
               f"Verification Code: {verification_code} This code is used to ensure the security of your account." \
               f" If you did not request this verification, please ignore this email." \
               f"Thank you, Mahdi Malvandi Social Media"

        send_mail(title, text, email)
        cache.set(email, verification_code, 60 * 2)

        user.save()

        return Response({'message': 'Verification code sent successfully'})


class GetUserToken(APIView): ...

# endregion
