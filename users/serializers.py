import re
from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model.
    """
    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'username', 'email', 'phone_number', 'profile', 'gender', 'date_of_birth', 'bio',
            'password')
        extra_kwargs = {'password': {"write_only": True}}

    def validate(self, data):
        """
        Validate user data.

        Parameters:
        - data: Data to be validated.

        Returns:
        - Validated data.
        """
        username = data['username']
        email = data['email']
        password = data['password']

        # Username Validation
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError('Username already exists')

        # Email Validation
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError('Email already exists')

        # Password Validation
        length = r'.{8,}'
        special_chars = r'[@#$%^&*(){}[\]]'
        digit = r'\d'
        uppercase = r'[A-Z]'
        lowercase = r'[a-z]'
        regex = f'^(?=.*{length})(?=.*{special_chars})(?=.*{digit})(?=.*{uppercase})(?=.*{lowercase}).+$'
        if not (8 <= len(password) and re.match(regex, password)):
            raise serializers.ValidationError('Password is Weak')

        return data

    def create(self, validated_data):
        """
        Create a new user instance.

        Parameters:
        - validated_data: Validated data.

        Returns:
        - New user instance.
        """
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Update an existing user instance.

        Parameters:
        - instance: Existing user instance.
        - validated_data: Validated data.

        Returns:
        - Updated user instance.
        """
        if 'password' in validated_data:
            validated_data['password'] = make_password(validated_data['password'])
        return super().update(instance, validated_data)


class UpdateUserSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile.
    """
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'phone_number', 'profile', 'gender')
        extra_kwargs = {
            "first_name": {"required": False},
            "last_name": {"required": False},
            "username": {"required": False},
            "email": {"required": False},
            "phone_number": {"required": False},
            "profile": {"required": False},
            "gender": {"required": False},
        }

    def validate_email(self, value):
        """
        Validate email field.

        Parameters:
        - value: Email value.

        Returns:
        - Validated email.
        """
        user = self.context['request'].user
        if User.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError({"email": "This email is already in use."})
        return value

    def validate_username(self, value):
        """
        Validate username field.

        Parameters:
        - value: Username value.

        Returns:
        - Validated username.
        """
        user = self.context['request'].user
        if User.objects.exclude(pk=user.pk).filter(username=value).exists():
            raise serializers.ValidationError({"username": "This username is already in use."})
        return value

    def update(self, instance, validated_data):
        """
        Update user instance.

        Parameters:
        - instance: Existing user instance.
        - validated_data: Validated data.

        Returns:
        - Updated user instance.
        """
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance


class RefreshTokenSerializer(serializers.Serializer):
    """
    Serializer for refreshing token.
    """
    refresh = serializers.CharField()

    default_error_messages = {
        'bad_token': 'Token is invalid or expired'
    }

    def validate(self, attrs):
        """
        Validate token.

        Parameters:
        - attrs: Token attributes.

        Returns:
        - Validated token.
        """
        self.token = attrs['refresh']
        return attrs

    def save(self, **kwargs):
        """
        Save refreshed token.

        Parameters:
        - kwargs: Additional keyword arguments.

        Returns:
        - None
        """
        try:
            RefreshToken(self.token).blacklist()
        except TokenError:
            self.fail('bad_token')
