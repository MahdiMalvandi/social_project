import re

from rest_framework import serializers
from users.models import *


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'phone_number', 'profile', 'gender', 'password')

    def validate(self, data):

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
