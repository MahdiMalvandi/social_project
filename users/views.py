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
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': 'Email or Username Cannot be empty'})
        try:
            if email is not None:
                user = User.objects.get(email=email)
            elif username is not None:
                user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'error': 'user not found'})

        if not user.is_auth:
            return Response(status=status.HTTP_403_FORBIDDEN, data={'error': 'User has to verify email'})
        if user.check_password(data['password']):
            cache_key = f'email_verification:{user.email}'
            cached_code = cache.get(cache_key)
            if cached_code is not None:
                return Response({'error': 'Verification code already sent'}, status=status.HTTP_400_BAD_REQUEST)
            return send_code(user.email)
        return Response({'error': 'Password is incorrect'}, status=status.HTTP_403_FORBIDDEN)


class RegisterAndSendEmail(APIView):
    permission_classes = [AllowAny]

    """
    Get User Data and Make an object and send verification email
    """

    def post(self, request, *args, **kwargs):
        data = request.data

        email = data['email'] if 'email' in data else None
        if email is None:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': 'Invalid email'})

        cache_key = f'email_verification:{email}'
        cached_code = cache.get(cache_key)
        if cached_code is not None:
            return Response({'error': 'Verification code already sent'}, status=status.HTTP_400_BAD_REQUEST)

        user = UserSerializer(data=data)
        if user.is_valid():
            user.save()
            return send_code(email)
        return Response({'error': user.errors}, status=status.HTTP_400_BAD_REQUEST)


class GetUserToken(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        user_email = request.data['email'] if 'email' in request.data else None
        verification_code = request.data['code'] if 'code' in request.data else None

        if user_email is None:
            return Response({'error': "Email cannot be empty"}, status=status.HTTP_400_BAD_REQUEST)

        if verification_code is None:
            return Response({'error': "Code cannot be empty"}, status=status.HTTP_400_BAD_REQUEST)

        cache_key = f'email_verification:{user_email}'

        stored_verification_code = cache.get(cache_key)

        if stored_verification_code == verification_code:
            user = User.objects.get(email=user_email)

            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token_str = str(refresh)
            cache.delete(cache_key)
            user.is_auth = True
            user.is_active = True
            user.save()
            response_data = {'access_token': access_token, 'refresh_token': refresh_token_str}
            return JsonResponse(response_data, status=status.HTTP_200_OK)
        elif stored_verification_code is None:
            return Response({"error": "The verification code either does not exist or has expired"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'detail': 'Invalid verification code'}, status=status.HTTP_401_UNAUTHORIZED)


class ResendCode(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        email = request.data['email'] if 'email' in request.data else None
        cache_key = f'email_verification:{email}'
        if email is None:
            return Response({'error': "Email cannot be empty"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': "User not found"})
        if user.is_auth:
            return Response({"error": "The user has already been verified and must login"},
                            status=status.HTTP_403_FORBIDDEN)
        stored_verification_code = cache.get(cache_key)
        if stored_verification_code is not None:
            cache.delete(stored_verification_code)

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


class ProfileApiView(APIView):
    def get(self, request, *args, **kwargs):
        current_user = request.user
        user_serializer = UserSerializer(current_user, context={"request": request})
        user_post_serializer = PostSerializer(current_user.posts.all(), many=True, context={"request": request})
        user_story_serializer = StorySerializer(current_user.stories.all(), many=True, context={"request": request})
        data = {
            'user_info': user_serializer.data,
            'posts': user_post_serializer.data,
            'stories': user_story_serializer.data,
        }
        return Response(data)

    def put(self, request, *args, **kwargs):
        serializer = UpdateUserSerializer(instance=request.user, data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class LogoutView(APIView):
    def post(self, request, *args):
        sz = RefreshTokenSerializer(data=request.data)
        sz.is_valid(raise_exception=True)
        sz.save()
        request.user.is_active = False
        return Response(status=status.HTTP_204_NO_CONTENT)
