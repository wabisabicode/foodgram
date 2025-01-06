from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .serializers import CustomUserSerializer, CustomUserCreateSerializer

User = get_user_model()


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    pagination_class = PageNumberPagination
    http_method_names = ['get', 'post']

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserCreateSerializer
        return CustomUserSerializer


class MeViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer = CustomUserSerializer
#    permission_classes = (IsAuthenticated,)
    http_method_names = ['get']

    def get(self, request):
        user = request.user
        serializer = CustomUserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # def patch(self, request):
    #     user = request.user
    #     serializer = UserSerializer(user, data=request.data, partial=True)
    #     serializer.is_valid(raise_exception=True)

    #     if 'role' in request.data:
    #         return Response(
    #             {'role': 'Modifying the role is not allowed.'},
    #             status=status.HTTP_400_BAD_REQUEST
    #         )

    #     serializer.save()
    #     return Response(serializer.data, status=status.HTTP_200_OK)