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


class LoginView(APIView):
    """
    API view for user login.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """
        Handle POST request for user login.

        Parameters:
        - request: Request object containing user data.
        - args: Additional arguments.
        - kwargs: Additional keyword arguments.

        Returns:
        - Response with login status and appropriate message.
        """
        data = request.data
        email = data.get('email')
        username = data.get('username')
        if not email and not username:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': 'Email or Username cannot be empty'})
        try:
            user = User.objects.get(email=email) if email else User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'error': 'User not found'})

        if not user.is_auth:
            return Response(status=status.HTTP_403_FORBIDDEN, data={'error': 'User has to verify email'})
        if user.check_password(data['password']):
            cache_key = f'email_verification:{user.email}'
            cached_code = cache.get(cache_key)
            if cached_code:
                return Response({'error': 'Verification code already sent'}, status=status.HTTP_400_BAD_REQUEST)
            return send_code(user.email)
        return Response({'error': 'Password is incorrect'}, status=status.HTTP_403_FORBIDDEN)


class RegisterAndSendEmail(APIView):
    """
    API view for user registration and sending verification email.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """
        Handle POST request for user registration and sending verification email.

        Parameters:
        - request: Request object containing user data.
        - args: Additional arguments.
        - kwargs: Additional keyword arguments.

        Returns:
        - Response with registration status and appropriate message.
        """
        data = request.data
        email = data.get('email')
        if not email:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': 'Invalid email'})

        cache_key = f'email_verification:{email}'
        cached_code = cache.get(cache_key)
        if cached_code:
            return Response({'error': 'Verification code already sent'}, status=status.HTTP_400_BAD_REQUEST)

        user = UserSerializer(data=data)
        if user.is_valid():
            user.save()
            return send_code(email)
        return Response({'error': user.errors}, status=status.HTTP_400_BAD_REQUEST)


class GetUserToken(APIView):
    """
    API view for getting user token after verification.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """
        Handle POST request for getting user token after verification.

        Parameters:
        - request: Request object containing user email and verification code.
        - args: Additional arguments.
        - kwargs: Additional keyword arguments.

        Returns:
        - Response with user token if verification successful.
        """
        user_email = request.data.get('email')
        verification_code = request.data.get('code')

        if not user_email:
            return Response({'error': "Email cannot be empty"}, status=status.HTTP_400_BAD_REQUEST)

        if not verification_code:
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
            return Response({"error": "The verification code either does not exist or has expired"},
                            status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'detail': 'Invalid verification code'}, status=status.HTTP_401_UNAUTHORIZED)


class ResendCode(APIView):
    """
    API view for resending verification code.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """
        Handle POST request for resending verification code.

        Parameters:
        - request: Request object containing user email.
        - args: Additional arguments.
        - kwargs: Additional keyword arguments.

        Returns:
        - Response with status of code resend.
        """
        email = request.data.get('email')
        cache_key = f'email_verification:{email}'
        if not email:
            return Response({'error': "Email cannot be empty"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': "User not found"})
        if user.is_auth:
            return Response({"error": "The user has already been verified and must login"},
                            status=status.HTTP_403_FORBIDDEN)
        stored_verification_code = cache.get(cache_key)
        if stored_verification_code:
            cache.delete(stored_verification_code)

        return send_code(email)


# endregion

class UserProfileView(APIView):
    """
    API view for user profile.
    """

    def get(self, request, username, *args, **kwargs):
        """
        Handle GET request for user profile.

        Parameters:
        - request: Request object.
        - username: Username of the requested user.
        - args: Additional arguments.
        - kwargs: Additional keyword arguments.

        Returns:
        - Response with user profile data.
        """
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response("User Not Found", status=status.HTTP_404_NOT_FOUND)
        user_serializer = UserSerializer(user, context={"request": request})
        user_post_serializer = PostSerializer(user.posts.all(), many=True, context={"request": request})
        user_story_serializer = StorySerializer(user.stories.all(), many=True, context={"request": request})
        is_following = user in request.user.following_users.all() if request.user.is_authenticated else False
        data = {
            'user_info': user_serializer.data,
            'posts': user_post_serializer.data,
            'stories': user_story_serializer.data,
            'is_following': is_following
        }
        return Response(data)


class UserFollowApi(APIView):
    """
    API view for user follow/unfollow functionality.
    """

    def post(self, request, username, *args, **kwargs):
        """
        Handle POST request for following/unfollowing a user.

        Parameters:
        - request: Request object.
        - username: Username of the user to follow/unfollow.
        - args: Additional arguments.
        - kwargs: Additional keyword arguments.

        Returns:
        - Response with follow status.
        """
        current_user = request.user
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response("User Not Found", status=status.HTTP_404_NOT_FOUND)
        obj, created = Follow.objects.get_or_create(follower=current_user, following=user)
        if created:
            return Response({'message': "following successfully", 'is_following': True}, status=status.HTTP_200_OK)
        else:
            obj.delete()
            return Response({'message': "unfollowing successfully", 'is_following': False}, status=status.HTTP_200_OK)


class ProfileApiView(APIView):
    """
    API view for user profile management.
    """

    def get(self, request, *args, **kwargs):
        """
        Handle GET request for user profile data.

        Parameters:
        - request: Request object.
        - args: Additional arguments.
        - kwargs: Additional keyword arguments.

        Returns:
        - Response with user profile data.
        """
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
        """
        Handle PUT request for updating user profile.

        Parameters:
        - request: Request object.
        - args: Additional arguments.
        - kwargs: Additional keyword arguments.

        Returns:
        - Response with updated user profile data.
        """
        serializer = UpdateUserSerializer(instance=request.user, data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class LogoutView(APIView):
    """
    API view for user logout.
    """

    def post(self, request, *args):
        """
        Handle POST request for user logout.

        Parameters:
        - request: Request object.
        - args: Additional arguments.

        Returns:
        - Response with logout status.
        """
        sz = RefreshTokenSerializer(data=request.data)
        sz.is_valid(raise_exception=True)
        sz.save()
        request.user.is_active = False
        return Response(status=status.HTTP_204_NO_CONTENT)
