# from django.shortcuts import render
# rest_framework.views import APIView
from django.contrib.auth import get_user_model
from rest_framework.viewsets import ModelViewSet

from .serializers import CustomUserSerializer

User = get_user_model()


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    http_method_names = ['get', 'post']
