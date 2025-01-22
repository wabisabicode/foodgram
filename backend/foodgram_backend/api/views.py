from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.views import APIView

from recipe.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                           RecipeShortURL, Tag)
from shopping_cart.models import ShoppingCartItem
from users.models import Subscription

from .filters import (FavoritesFilterBackend, IngredientFilterBackend,
                      ShoppingCartFilterBackend, TagsFilterBackend)
from .pagination import PageLimitPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (AvatarSerializer, CreatorSerializer,
                          CustomUserCreateSerializer, CustomUserSerializer,
                          IngredientSerializer, RecipeWriteSerializer,
                          RecipeShortURLSerializer, SetPasswordSerializer,
                          ShortRecipeSerializer, TagReadSerializer,
                          TokenCreateSerializer)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    pagination_class = PageLimitPagination
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

        subscription = Subscription.objects.filter(
            subscriber=subscriber, creator=creator)

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

            subscription = Subscription.objects.create(
                subscriber=subscriber, creator=creator)
            serializer = CreatorSerializer(
                creator, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if subscription.exists():
                subscription.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)


class MySubscriptions(APIView):
    permission_classes = (IsAuthenticated,)
    pagination_class = PageLimitPagination

    def get(self, request):
        subscriptions = request.user.following.all()
        creators = [subscription.creator for subscription in subscriptions]

        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(creators, request)

        serializer = CreatorSerializer(
            result_page, context={'request': request}, many=True)

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
        serializer = SetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_password = serializer.validated_data.get('new_password')
        current_password = serializer.validated_data.get('current_password')

        user = request.user

        if not user.check_password(current_password):
            raise ValidationError('Invalid current password')

        user.set_password(new_password)
        user.save()

        return Response('Password has been changed',
                        status=status.HTTP_204_NO_CONTENT)


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
    serializer_class = TagReadSerializer
    pagination_class = None


class IngredientListRetrieveViewSet(mixins.ListModelMixin,
                                    mixins.RetrieveModelMixin,
                                    viewsets.GenericViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (IngredientFilterBackend,)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly, IsAuthenticatedOrReadOnly)
    serializer_class = RecipeWriteSerializer
    filter_backends = (DjangoFilterBackend, TagsFilterBackend,
                       FavoritesFilterBackend, ShoppingCartFilterBackend)
    filterset_fields = ('author', 'tags__slug')
    pagination_class = PageLimitPagination

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
        shopping_cart_item = ShoppingCartItem.objects.filter(
            user=user, recipe=recipe)

        if request.method == 'POST':
            if shopping_cart_item.exists():
                return Response(
                    {'detail': 'Cannot add to the shopping cart twice'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            shopping_cart_item = ShoppingCartItem.objects.create(
                recipe=recipe, user=user)
            serializer = ShortRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if shopping_cart_item.exists():
                shopping_cart_item.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_shopping_cart(request):
    cart_recipes = Recipe.objects.filter(
        shopping_cart_items__user=request.user)

    shopping_list = {}
    for recipe in cart_recipes:
        for ingredient in recipe.ingredients.all():
            recipe_ingredient = get_object_or_404(
                RecipeIngredient, ingredient=ingredient, recipe=recipe)
            amount = recipe_ingredient.amount
            measurement_unit = recipe_ingredient.ingredient.measurement_unit
            if ingredient.name in shopping_list.keys():
                shopping_list[ingredient.name][0] += amount
            else:
                shopping_list[ingredient.name] = [amount, measurement_unit]

    shopping_list_items = '\n'.join(
        f'{item}: {amount} {unit}'
        for item, (amount, unit) in shopping_list.items()
    )

    return HttpResponse(
        shopping_list_items,
        headers={
            "Content-Type": "text/plain",
            # "Content-Type": "text/csv",
            # "Content-Type": "application/pdf",
            "Content-Disposition": 'attachment; filename="shopping_list.txt"',
        },
    )
