from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from recipe.models import (Favorite, Ingredient, Recipe, RecipeShortURL,
                           ShoppingCartItem, Tag)
from users.models import Subscription

from .filters import IngredientFilter, RecipeFilter
from .pagination import PageLimitPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (AvatarSerializer, CreatorSerializer,
                          CustomUserCreateSerializer, CustomUserSerializer,
                          IngredientSerializer, RecipeShortURLSerializer,
                          RecipeWriteSerializer, SetPasswordSerializer,
                          ShortRecipeSerializer, TagReadSerializer)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = (IsAuthenticated,)
    pagination_class = PageLimitPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserCreateSerializer
        return CustomUserSerializer

    def get_permissions(self):
        if self.action in ['create', 'list', 'retrieve']:
            return [AllowAny()]
        if self.action == 'toggle_subscription':
            return [IsAuthorOrReadOnly(), IsAuthenticated()]
        return super().get_permissions()

    @action(methods=['POST', 'DELETE'], detail=True, url_path='subscribe')
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

    @action(methods=['GET'], detail=False, url_path='subscriptions')
    def get_mysubscriptions(self, request):
        subscriptions = request.user.following.all()
        creators = [subscription.creator for subscription in subscriptions]
        result_page = self.paginate_queryset(creators)

        serializer = CreatorSerializer(
            result_page, context={'request': request}, many=True)

        return self.get_paginated_response(serializer.data)

    @action(methods=['GET'], detail=False, url_path='me')
    def me_page(self, request):
        user = request.user
        serializer = CustomUserSerializer(user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['PUT'], detail=False, url_path='me/avatar')
    def avatar(self, request):
        serializer = AvatarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.avatar = serializer.validated_data.get('avatar')
        user.save()

        avatar_url = serializer.get_avatar_url(user)
        return Response({'avatar': avatar_url}, status=status.HTTP_200_OK)

    @avatar.mapping.delete
    def delete_avatar(self, request):
        user = request.user
        user.avatar.delete()
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['POST'], detail=False, url_path='set_password')
    def set_password(self, request):
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


class TagListRetrieveViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagReadSerializer
    pagination_class = None


class IngredientListRetrieveViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.select_related(
        'author').prefetch_related('ingredients', 'tags')
    permission_classes = (IsAuthorOrReadOnly, IsAuthenticatedOrReadOnly)
    serializer_class = RecipeWriteSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
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
        return self.toggle_parameter(request, Favorite, pk)

    @action(methods=['POST', 'DELETE'], detail=True, url_path='shopping_cart')
    def toggle_shopping_cart_item(self, request, pk):
        return self.toggle_parameter(request, ShoppingCartItem, pk)

    def toggle_parameter(self, request, Model, pk):
        user = request.user
        recipe = get_object_or_404(self.get_queryset(), pk=pk)
        object = Model.objects.filter(user=user, recipe=recipe)

        if request.method == 'POST':
            if object.exists():
                return Response(
                    {'detail': 'Cannot select object twice'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            Model.objects.create(recipe=recipe, user=user)
            serializer = ShortRecipeSerializer(recipe)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            deleted, _ = object.delete()
            if not deleted:
                raise ValidationError('Recipe not in shopping cart')
            return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_shopping_cart(request):
    ingredients = (
        Ingredient.objects.filter(
            recipes__shopping_cart_items__user=request.user)
        .annotate(total_amount=Sum('recipeingredients__amount'))
        .values('name', 'measurement_unit', 'total_amount')
    )

    shopping_list_items = '\n'.join(
        f'{ingredient['name']}: '
        f'{ingredient['total_amount']} '
        f'{ingredient['measurement_unit']}'
        for ingredient in ingredients
    )

    return HttpResponse(
        shopping_list_items,
        headers={
            "Content-Type": "text/plain",
            "Content-Disposition": 'attachment; filename="shopping_list.txt"',
        },
    )
