from django.core.cache import cache
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from .functions import send_code
from users.models import User
from .serializers import *
from posts.serializers import PostSerializer, StorySerializer
from posts.models import Post


# region login and registration
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        data = request.data
        email = data['email'] if 'email' in data else None
        username = data['username'] if 'username' in data else None
        if email is None and username is None:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': 'Invalid email or username'})
        try:
            if username is not None:
                user = User.objects.get(username=username)
            elif email is not None:
                user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'error': 'user not found'})

        if not user.is_auth:
            return Response(status=status.HTTP_403_FORBIDDEN, data={'error': 'User has to verify email'})
        if user.check_password(data['password']):
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token_str = str(refresh)
            response_data = {'access_token': access_token, 'refresh_token': refresh_token_str}
            return JsonResponse(response_data, status=status.HTTP_200_OK)
        return Response({'error': 'Password is incorrect'}, status=status.HTTP_403_FORBIDDEN)


class RegisterAndSendEmail(APIView):
    """
    Get User Data and Make an object and send verification email
    """

    def post(self, request, *args, **kwargs):
        permission_classes = [AllowAny]

        data = request.data

        email = data['email'] if 'email' in data else None
        if email is None:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': 'Invalid email'})

        cache_key = f'email_verification:{email}'
        cached_code = cache.get(cache_key)
        if cached_code is not None:
            return Response({'error': 'Verification code already sent'}, status=status.HTTP_400_BAD_REQUEST)

        user = UserRegisterSerializer(data=data)
        if user.is_valid():
            user.save()
            return send_code(email)
        return Response({'error': user.errors}, status=status.HTTP_400_BAD_REQUEST)


class GetUserToken(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        user_email = request.data.get('email', '')
        verification_code = request.data.get('code', '')

        cache_key = f'email_verification:{user_email}'

        stored_verification_code = cache.get(cache_key)

        if stored_verification_code == verification_code:
            user = User.objects.get(email=user_email)

            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token_str = str(refresh)
            cache.delete(cache_key)
            user.is_auth = True
            user.save()
            response_data = {'access_token': access_token, 'refresh_token': refresh_token_str}
            return JsonResponse(response_data, status=status.HTTP_200_OK)
        elif stored_verification_code is None:
            return Response({"error": "There is no code"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'detail': 'Invalid verification code'}, status=status.HTTP_401_UNAUTHORIZED)


class ResendCode(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        email = request.data['email']
        cache_key = f'email_verification:{email}'

        stored_verification_code = cache.get(cache_key)
        if stored_verification_code is not None:
            return Response({'error': 'verification code sent successfully'}, status=status.HTTP_403_FORBIDDEN)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': "User not found"})

        if user.is_auth:
            return Response({"error": "The user has already been verified and must login"},
                            status=status.HTTP_403_FORBIDDEN)

        return send_code(email)


# endregion

class UserProfileView(APIView):
    def get(self, request, username, *args, **kwargs):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response("User Not Found", status=status.HTTP_404_NOT_FOUND)
        user_serializer = UserSerializer(user, context={"request": request})
        user_post_serializer = PostSerializer(user.posts.all(), many=True, context={"request": request})
        user_story_serializer = StorySerializer(user.stories.all(), many=True, context={"request": request})
        if user in request.user.following_users:
            is_following = True
        else:
            is_following = False
        data = {
            'user_info': user_serializer.data,
            'posts': user_post_serializer.data,
            'stories': user_story_serializer.data,
            'is_following': is_following
        }
        return Response(data)


class UserFollowApi(APIView):
    def post(self, request, username, *args, **kwargs):
        current_user = request.user
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response("User Not Found", status=status.HTTP_404_NOT_FOUND)
        obj, created = Follow.objects.get_or_create(follower=current_user, following=user)
        if created:
            return Response({'message': "following successfully", 'is_following': True}, status=status.HTTP_200_OK)
        else:
            return Response({'message': "unfollowing successfully", 'is_following': False}, status=status.HTTP_200_OK)

