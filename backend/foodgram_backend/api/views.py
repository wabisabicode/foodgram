from django.contrib.auth import authenticate, get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
# from djoser.serializers import TokenSerializer
from django.shortcuts import get_object_or_404

from .serializers import CustomUserSerializer, CustomUserCreateSerializer
from .serializers import TokenCreateSerializer

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


class TokenCreateView(APIView):

    def post(self, request):
        serializer = TokenCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get('email')
        password = serializer.validated_data.get('password')

        user = get_object_or_404(User, email=email)

        # user = authenticate(request, email=email, password=password)
        # print(user)
        # if user is None:
        # if user.password != password:
        if not user.check_password(password):
            raise AuthenticationFailed('Invalid credentialsss')

        # token = Token.objects.create(user=user)
        token, created = Token.objects.get_or_create(user=user)

        return Response({'auth_token': str(token)}, status=status.HTTP_200_OK)


class TokenLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token = Token.objects.get(user=request.user)
        token.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
