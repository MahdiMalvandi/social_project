import random
import string

from django.core.cache import cache
from django.core.mail import send_mail
from .serializers import *
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import User
from social_project.settings import EMAIL_HOST_USER


# region login and registration
class LoginView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        email = data['email'] if 'email' in data else None
        if email is None:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': 'Invalid email'})
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'error':'user not found'})

        if not user.is_auth:
            return Response(status=status.HTTP_403_FORBIDDEN, data={'error':'User has to verify email'})
        if user.check_password(data['password']):
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            return Response({'access_token': access_token, 'refresh_token': refresh}, status=status.HTTP_200_OK)
        return Response({'error': 'Password is incorrect'}, status=status.HTTP_403_FORBIDDEN)


class RegisterAndSendEmail(APIView):
    """
    Get User Data and Make an object and send verification email
    """

    def post(self, request, *args, **kwargs):
        data = request.data

        email = data['email'] if 'email' in data else None
        if email is None:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': 'Invalid email'})

        cached_code = cache.get(email)
        if cached_code is not None:
            return Response({'error': 'Verification code already sent'}, status=status.HTTP_400_BAD_REQUEST)

        user = UserSerializer(data=data)
        if user.is_valid():
            user.save()
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

            send_mail(title, text, EMAIL_HOST_USER, [email])
            cache.set(email, verification_code, 60 * 2)

            return Response({'email': email, 'code': verification_code})
        return Response({'error': user.errors}, status=status.HTTP_400_BAD_REQUEST)


class GetUserToken(APIView):
    def post(self, request, *args, **kwargs):
        user_email = request.data.get('email', '')
        verification_code = request.data.get('code', '')

        cache_key = f'code:{user_email}'
        cache.set(user_email, verification_code, 60 * 2)
        stored_verification_code = cache.get(cache_key)

        if stored_verification_code == verification_code:
            user = User.objects.get(email=user_email)

            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            cache.delete(cache_key)
            user.is_auth = True
            return Response({'access_token': access_token, 'refresh_token': refresh}, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'Invalid verification code'}, status=status.HTTP_401_UNAUTHORIZED)

# endregion
