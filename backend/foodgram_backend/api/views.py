from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.pagination import (
    LimitOffsetPagination, PageNumberPagination)
from rest_framework.permissions import (
    AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import CustomUserSerializer, CustomUserCreateSerializer
from .serializers import SetPasswordSerializer, TokenCreateSerializer
from .serializers import AvatarSerializer, TagSerializer, IngredientSerializer
from .serializers import RecipeSerializer, FavoriteSerializer
from recipe.models import Tag, Ingredient, Recipe, Favorite

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    pagination_class = LimitOffsetPagination
    http_method_names = ['get', 'post']

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserCreateSerializer
        return CustomUserSerializer


class MeView(APIView):
    # queryset = User.objects.all()
    # serializer_class = CustomUserSerializer
    permission_classes = (IsAuthenticated,)
    # http_method_names = ['get']

    def get(self, request):
        print('Get-Request to ME!!!!!')
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


class SetPasswordView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        print("SetPasswordView POST called")
        serializer = SetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_password = serializer.validated_data.get('new_password')
        current_password = serializer.validated_data.get('current_password')

        user = request.user

        if not user.check_password(current_password):
            raise AuthenticationFailed('Invalid credentials')
        else:
            user.set_password(new_password)
            user.save()

        return Response('Password has been changed', status=status.HTTP_200_OK)


class TokenCreateView(APIView):

    def post(self, request):
        serializer = TokenCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get('email')
        password = serializer.validated_data.get('password')

        user = get_object_or_404(User, email=email)

        if not user.check_password(password):
            raise AuthenticationFailed('Invalid credentials')

        token, created = Token.objects.get_or_create(user=user)

        return Response({'auth_token': str(token)}, status=status.HTTP_200_OK)


class TokenLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token = Token.objects.get(user=request.user)
        token.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class AvatarView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = AvatarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        user.avatar = serializer.validated_data.get('avatar')
        user.save()

        avatar_url = serializer.get_avatar_url(user)

        return Response({'avatar': avatar_url}, status=status.HTTP_200_OK)

    def delete(self, request):
        user = request.user

        user.avatar.delete()
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagListRetrieveViewSet(mixins.ListModelMixin,
                             mixins.RetrieveModelMixin,
                             viewsets.GenericViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientListRetrieveViewSet(mixins.ListModelMixin,
                                    mixins.RetrieveModelMixin,
                                    viewsets.GenericViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_fields = ('name',)
    search_fields = ('^name',)
    pagination_class = None


# class ConditionalPagination(LimitOffsetPagination):
#     def paginate_queryset(self, queryset, request, view=None):
#         if request.query_params:
#             return None
#         return super().paginate_queryset(queryset, request, view)

#     def get_paginated_response(self, data):
#         return super().get_paginated_response(data)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = RecipeSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = (
        # 'is_favorited', 'is_in_shopping_cart',
        'author', 'tags__slug')
    pagination_class = LimitOffsetPagination  # ConditionalPagination


class FavoriteViewSet(mixins.CreateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer
