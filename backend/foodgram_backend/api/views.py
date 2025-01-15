from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import (
    AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import IsAuthorOrReadOnly
from .serializers import CustomUserSerializer, CustomUserCreateSerializer
from .serializers import SetPasswordSerializer, TokenCreateSerializer
from .serializers import AvatarSerializer, TagSerializer, IngredientSerializer
from .serializers import RecipeSerializer  # , FavoriteSerializer
from .serializers import RecipeShortURLSerializer, ShortRecipeSerializer
from .serializers import CreatorSerializer
from recipe.models import Tag, Ingredient, Recipe, Favorite, RecipeShortURL
from users.models import Subscription
from shopping_cart.models import ShoppingCartItem

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    pagination_class = LimitOffsetPagination
    http_method_names = ['get', 'post', 'delete']

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserCreateSerializer
        return CustomUserSerializer

    @action(methods=['POST', 'DELETE'], detail=True, url_path='subscribe',
            permission_classes=[IsAuthorOrReadOnly, IsAuthenticated])
    def toggle_subscription(self, request, pk=None):
        subscriber = request.user
        creator = get_object_or_404(User, pk=pk)

        subscription = Subscription.objects.filter(subscriber=subscriber, creator=creator)

        if request.method == 'POST':
            if subscription.exists():
                return Response(
                    {'detail': 'Cannot subscribe twice'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if subscriber == creator:
                return Response(
                    {'detail': 'Cannot subscribe to myself'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            subscription = Subscription.objects.create(subscriber=subscriber, creator=creator)
            serializer = CreatorSerializer(creator, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if subscription.exists():
                subscription.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)


class MySubscriptions(APIView):
    permission_classes = (IsAuthenticated,)
    pagination_class = LimitOffsetPagination

    def get(self, request):
        subscriptions = request.user.following.all()
        creators = [subscription.creator for subscription in subscriptions]

        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(creators, request)

        serializer = CreatorSerializer(result_page, context={'request': request}, many=True)

        return paginator.get_paginated_response(serializer.data)


class MeView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        serializer = CustomUserSerializer(user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


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
            raise ValidationError('Invalid current password')
        else: # delete else and move the code below to the left? 
            user.set_password(new_password)
            user.save()

        return Response('Password has been changed', status=status.HTTP_204_NO_CONTENT)


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


class TagsFavoritesFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        tags = request.query_params.getlist('tags', [])

        if tags:
            return queryset.filter(tags__slug__in=tags)

        is_favorited = request.query_params.get('is_favorited', None)
        if is_favorited is not None:
            if not request.user.is_authenticated:
                return queryset.none()
            recipes = Recipe.objects.filter(favorites__user=request.user)
            return recipes

        return queryset


class ShoppingCartFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        is_in_shopping_cart = request.query_params.get('is_in_shopping_cart', None)

        print(f'is_in_shopping_cart: {is_in_shopping_cart}')
        if is_in_shopping_cart is not None:
            if not request.user.is_authenticated:
                return queryset.none()
            recipes = Recipe.objects.filter(shopping_cart_items__user=request.user)
            return recipes

        return queryset



class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly, IsAuthenticatedOrReadOnly)
    serializer_class = RecipeSerializer
    filter_backends = (DjangoFilterBackend, TagsFavoritesFilterBackend, ShoppingCartFilterBackend)
    filterset_fields = (
        # 'is_in_shopping_cart',
        'author', 'tags__slug')
    pagination_class = LimitOffsetPagination  # ConditionalPagination

    @action(detail=True, url_path='get-link')
    def get_short_link(self, request, pk):
        short_url = RecipeShortURL.objects.get(recipe__id=pk)

        serializer = RecipeShortURLSerializer(
            short_url, context={'request': request})

        return Response(
            {'short-link': serializer.data['short_link']},
            status=status.HTTP_200_OK
        )

    @action(methods=['POST', 'DELETE'], detail=True, url_path='favorite')
    def set_favorite(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        favorite = Favorite.objects.filter(recipe=recipe, user=request.user)

        if request.method == 'POST':
            if favorite.exists():
                return Response(
                    {'detail': 'Cannot add to the favorites twice'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            favorite = Favorite.objects.create(recipe=recipe, user=user)
            serializer = ShortRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if favorite.exists():
                favorite.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['POST', 'DELETE'], detail=True, url_path='shopping_cart')
    def toggle_shopping_cart_item(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        shopping_cart_item = ShoppingCartItem.objects.filter(user=user, recipe=recipe)

        if request.method == 'POST':
            if shopping_cart_item.exists():
                return Response(
                    {'detail': 'Cannot add to the shopping cart twice'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            shopping_cart_item = ShoppingCartItem.objects.create(recipe=recipe, user=user)
            serializer = ShortRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if shopping_cart_item.exists():
                shopping_cart_item.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)


def shortURLRedirect(request, hash):
    recipe_short_url = get_object_or_404(RecipeShortURL, hash=hash)
    recipe_detail_url = reverse(
        'api:recipes-detail', kwargs={'pk': recipe_short_url.recipe.pk})
    return redirect(recipe_detail_url)


# class FavoriteViewSet(mixins.CreateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
#     permission_classes = (IsAuthenticated,)
#     queryset = Favorite.objects.all()
#     serializer_class = FavoriteSerializer
