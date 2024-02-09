import re

from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from .models import *


class UserRegisterSerializer(serializers.ModelSerializer):
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

    def create(self, validated_data):

        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)

    def update(self, instance, validated_data):

        if 'password' in validated_data:
            validated_data['password'] = make_password(validated_data['password'])
        return super().update(instance, validated_data)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'username', 'email', 'phone_number', 'profile', 'gender', 'date_of_birth', 'bio')

