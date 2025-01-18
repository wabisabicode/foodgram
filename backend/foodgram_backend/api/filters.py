from rest_framework import filters

from recipe.models import Ingredient, Recipe


class TagsFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        tags = request.query_params.getlist('tags', [])

        if tags:
            return queryset.filter(tags__slug__in=tags).distinct()

        return queryset


class IngredientFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        lookup_value = request.query_params.get('name', None)

        if lookup_value is not None:
            ingredients = Ingredient.objects.filter(
                name__startswith=lookup_value.lower())
            return ingredients

        return queryset


class FavoritesFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        is_favorited = request.query_params.get('is_favorited', None)

        if is_favorited is not None:
            if not request.user.is_authenticated:
                return queryset.none()
            recipes = Recipe.objects.filter(favorites__user=request.user)
            return recipes

        return queryset


class ShoppingCartFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        is_in_shopping_cart = request.query_params.get(
            'is_in_shopping_cart', None)

        if is_in_shopping_cart is not None:
            if not request.user.is_authenticated:
                return queryset.none()
            recipes = Recipe.objects.filter(
                shopping_cart_items__user=request.user)
            return recipes

        return queryset
