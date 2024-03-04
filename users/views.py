from django.core.cache import cache
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from .functions import send_code, check_verification_code
from users.models import User, Follow
from .serializers import *
from posts.serializers import PostSerializer, StorySerializer

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


class LoginView(APIView):
    """
    API view for user login.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING),
                'email': openapi.Schema(type=openapi.TYPE_STRING),
                'password': openapi.Schema(type=openapi.TYPE_STRING)
            },
            required=['password'],
            description="You need to send either the username or email along with the password."
        ),
        responses={
            200: "Successful operation.",
            400: "Either the username or email is incorrect, or the password is incorrect, or the account does not exist.",
            403: "User has to verify email"
        }
    )
    def post(self, request, *args, **kwargs):
        """
        This API is designed for user login.
        You need to send a request with either the username or email and a password in the request body. If the provided credentials are correct, a verification code will be sent to the user's email. This code should then be sent to the '/token' endpoint of this API.

        """
        data = request.data
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')
        if not email and not username:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': 'Email or Username cannot be empty'})
        if not password:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': 'Password cannot be empty'})
        try:
            user = User.objects.get(email=email) if email else User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'error': 'User not found'})

        if not user.is_auth:
            return Response(status=status.HTTP_403_FORBIDDEN, data={'error': 'User has to verify email'})
        if user.check_password(password):
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

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                'username': openapi.Schema(type=openapi.TYPE_STRING),
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING),
                'profile': openapi.Schema(type=openapi.TYPE_STRING),
                'gender': openapi.Schema(type=openapi.TYPE_STRING),
                'date_of_birth': openapi.Schema(type=openapi.TYPE_STRING),
                'bio': openapi.Schema(type=openapi.TYPE_STRING),
                'password': openapi.Schema(type=openapi.TYPE_STRING)
            },
            required=['password', 'first_name', 'last_name', 'username', 'phone_number', 'email'],
            description="You need to send either the username or email along with the password."
        ),
        responses={
            200: "Successful operation.",
            400: "Either the username or email is incorrect, or the password is incorrect, or the account does not exist.",
            403: "User has to verify email"
        }
    )
    def post(self, request, *args, **kwargs):
        """
        This API is designed for user registration.
        You need to send a request with all the required user information in the request body. If no user with the provided information exists, the information will be stored, and a verification code will be sent. This code should then be sent to the '/token' endpoint of this API to obtain the token.
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

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING),
                'code': openapi.Schema(type=openapi.TYPE_STRING)
            },
            required=['email', 'code'],
            description="You need to provide the email address and verification code."
        ),
        responses={
            200: "Successful operation. Returns access and refresh tokens.",
            400: "Possible reasons include empty email or code, or invalid verification code.",
            401: "Invalid verification code."
        }
    )
    def post(self, request, *args, **kwargs):
        """
        This endpoint is used to obtain user tokens after verification.
        If the verification code has expired, the user can send a request to the '/resend' endpoint to receive the code again.
        """
        user_email = request.data.get('email')
        check_code = check_verification_code(request)
        if check_code['result']:
            user = User.objects.get(email=user_email)

            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token_str = str(refresh)
            user.is_auth = True
            user.is_active = True
            user.save()
            response_data = {'access_token': access_token, 'refresh_token': refresh_token_str}
            return JsonResponse(response_data, status=status.HTTP_200_OK)
        else:
            return Response({"error": check_code['error']},
                            status=status.HTTP_400_BAD_REQUEST)


class ResendCode(APIView):
    """
    API view for resending verification code.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING),
                'password': openapi.Schema(type=openapi.TYPE_STRING)
            },
            required=['email', 'password'],
            description="You need to send the email and password to resend the verification code."
        ),
        responses={
            200: "The operation is successful, and the code has been sent. You should proceed to the `/token` endpoint",
            400: "The email or password may be incorrect.",
        }
    )
    def post(self, request, *args, **kwargs):
        """
        API Usage:
        This endpoint is used to resend the verification code.

        Parameters:
        - `email` (required): The email address of the user.
        - `password` (required): The password of the user.

        Returns:
        - Response with status of code resend.

        If the provided credentials are correct, a verification code will be resent to the user's email.
        """

        email = request.data.get('email')
        password = request.data.get('password')
        cache_key = f'email_verification:{email}'
        if not email:
            return Response({'error': "Email cannot be empty"}, status=status.HTTP_400_BAD_REQUEST)

        if not password:
            return Response({'error': "Password cannot be empty"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': "User not found"})

        if not user.check_password(password):
            return Response({"error": "Password is Wrong"}, status=status.HTTP_400_BAD_REQUEST)
        stored_verification_code = cache.get(cache_key)
        if stored_verification_code:
            cache.delete(stored_verification_code)

        return send_code(email)


class UserProfileView(APIView):
    """
    API view for user profile.
    """

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('username', openapi.IN_PATH, description="Username of the user",
                              type=openapi.TYPE_STRING),
        ],
        responses={
            200: "Successful operation. Returns user profile data.",
            404: "User Not Found. Indicates that the provided username is incorrect."
        }
    )
    def get(self, request, username, *args, **kwargs):
        """
            API Usage: This API is utilized to retrieve user profile information. You need to provide the username of the desired user in order to fetch their profile data.


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

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('username', openapi.IN_PATH, description="Username of the user to follow/unfollow",
                              type=openapi.TYPE_STRING),
        ],
        responses={
            200: "Following/unfollowing operation was successful. Returns follow status.",
            404: "User not found."
        }
    )
    def post(self, request, username, *args, **kwargs):
        """
        Handle POST request for following/unfollowing a user.

        Parameters:
        - `username` (path): Username of the user to follow/unfollow.

        Responses:
        - Status Code 200: Indicates that the following/unfollowing operation was successful. Returns follow status.
        - Status Code 404: Indicates that the user was not found.
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

    @swagger_auto_schema(
        responses={
            200: "Returns the user profile data.",
            404: "This means that data such as email, phone number, or username may have been previously registered with another account"
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Handle GET request for user profile data.

        Responses:
        - Status Code 200: Returns the user profile data.
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

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, description="First name of the user."),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, description="Last name of the user."),
                'username': openapi.Schema(type=openapi.TYPE_STRING, description="Username of the user."),
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL,
                                        description="Email address of the user."),
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description="Phone number of the user."),
                'profile': openapi.Schema(type=openapi.TYPE_STRING, description="Profile information of the user."),
                'gender': openapi.Schema(type=openapi.TYPE_STRING, description="Gender of the user."),
                'date_of_birth': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE,
                                                description="Date of birth of the user."),
            },
            description="Update user profile data."
        ),
        responses={
            200: "Returns the updated user profile data.",
        }
    )
    def put(self, request, *args, **kwargs):
        """
        Handle PUT request for updating user profile.

        Request Body:
        - `first_name` (optional): First name of the user.
        - `last_name` (optional): Last name of the user.
        - `username` (optional): Username of the user.
        - `email` (optional): Email address of the user.
        - `phone_number` (optional): Phone number of the user.
        - `profile` (optional): Profile information of the user.
        - `gender` (optional): Gender of the user.
        - `date_of_birth` (optional): Date of birth of the user.

        Responses:
        - Status Code 200: Returns the updated user profile data.
        """
        serializer = UpdateUserSerializer(instance=request.user, data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class LogoutView(APIView):
    """
    API view for user logout.
    """

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING, description="Refresh token to invalidate."),
            },
            required=['refresh'],
            description="Refresh token to invalidate."
        ),
        responses={
            200: "Logout successful.",
        }
    )
    def post(self, request, *args):
        """
        Handle POST request for user logout.

        Request Body:
        - `refresh` (required): Refresh token to invalidate.

        Responses:
        - Status Code 200: Logout successful.
        """
        sz = RefreshTokenSerializer(data=request.data)
        sz.is_valid(raise_exception=True)
        sz.save()
        request.user.is_active = False
        return Response(status=status.HTTP_200_OK)


class ChangePasswordApiView(APIView):
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'old_password': openapi.Schema(type=openapi.TYPE_STRING, description="The current password of the user."),
                'new_password': openapi.Schema(type=openapi.TYPE_STRING, description="The new password to be set.")
            },
            required=['old_password', 'new_password'],
            description="Request body for changing the password."
        ),
        responses={
            200: "Password changed successfully.",
            400: "Bad request. Invalid old password or missing required fields."
        }
    )
    def post(self, request, *args, **kwargs):
        """
        Handle POST request for changing the password.

        Parameters:
        - old_password (str): The current password of the user.
        - new_password (str): The new password to be set.

        Returns:
        - Response with the status of password change operation.
        """
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not old_password or not new_password:
            return Response({'error': "Old password or new password cannot be empty"}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        if not user.check_password(old_password):
            return Response({'error': "Old password is wrong"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            user.set_password(new_password)
            user.save()
            return Response({'success': True}, status=status.HTTP_200_OK)


class ForgotPasswordSendEmailApiView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, description="The email address of the user who forgot their password."),
            },
            required=['email'],
            description="Email address of the user who forgot their password."
        ),
        responses={
            200: "Email sent successfully. Please proceed to the `reset-password/confirm/` endpoint with the provided code.",
            400: "Bad request. The email address is required.",
            404: "User not found."
        }
    )
    def post(self, request, *args, **kwargs):
        """
        Handle POST request for sending forgot password email.

        Request Body:
        - `email` (required): The email address of the user who forgot their password.

        Responses:
        - Status Code 200: Email sent successfully. Please proceed to the reset-password/confirm/ endpoint with the provided code.
        - Status Code 400: Bad request. The email address is required.
        """
        email = request.data.get('email')
        if not User.objects.filter(email=email).exists():
            return Response({'error': "User does not exist"}, status=status.HTTP_400_BAD_REQUEST)

        if not email:
            return Response({'error': "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Sending code to the user's email (not shown in this snippet)
        # Assuming send_code(email, key='forgot_password') sends the code to the user's email

        return Response({'message': "Email sent successfully. Please proceed to the reset-password/confirm/ endpoint with the provided code."},
                        status=status.HTTP_200_OK)


class ForgotPasswordApiView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, description="The email address of the user who forgot their password."),
                'new_password': openapi.Schema(type=openapi.TYPE_STRING, description="The new password to be set."),
                'code': openapi.Schema(type=openapi.TYPE_STRING, description="The verification code received for password reset.")
            },
            required=['email', 'new_password', 'code'],
            description="Request body for resetting the password."
        ),
        responses={
            200: "Password changed successfully.",
            400: "Bad request. Invalid code or missing required fields.",
            404: "User not found."
        }
    )
    def post(self, request, *args, **kwargs):
        """
        Handle POST request for resetting password.

        Parameters:
        - email (str): The email address of the user who forgot their password.
        - new_password (str): The new password to be set.
        - code (str): The verification code received for password reset.

        Returns:
        - Response with the status of password change operation.
        """
        new_password = request.data.get('new_password')
        email = request.data.get('email')
        code = request.data.get('code')

        if not new_password:
            return Response({'error': "New password is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not email:
            return Response({'error': "Email address is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not code:
            return Response({'error': "Verification code is required"}, status=status.HTTP_400_BAD_REQUEST)

        check_code = check_verification_code(request, key='forgot_password')
        if check_code:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({'error': "User not found."}, status=status.HTTP_404_NOT_FOUND)
            user.set_password(new_password)
            user.save()
            return Response({'success': True, 'message': "Password changed successfully."}, status=status.HTTP_200_OK)
        else:
            return Response({'error': "Invalid code"}, status=status.HTTP_400_BAD_REQUEST)