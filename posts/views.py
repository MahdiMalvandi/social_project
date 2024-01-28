from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from .serializers import *


class PostsApiView(APIView):
    def get(self, request, *args, **kwargs):
        posts = Post.actives.all()
        serializer = PostSerializer(posts, many=True,context={'request': request})
        return Response({'data': serializer.data})
