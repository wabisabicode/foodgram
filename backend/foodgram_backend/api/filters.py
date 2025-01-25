from django_filters import rest_framework as filters

from recipe.models import Ingredient, Recipe


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(method='filter_by_name', label="Name")

    class Meta:
        model = Ingredient
        fields = ['name']

    def filter_by_name(self, queryset, name, value):
        if value:
            return queryset.filter(name__startswith=value.lower())
        return queryset


class RecipeFilter(filters.FilterSet):
    tags = filters.CharFilter(method='filter_tags')
    is_favorited = filters.BooleanFilter(
        method='filter_favorites')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_shopping_cart')
    author = filters.NumberFilter(field_name='author__id')

    class Meta:
        model = Recipe
        fields = ['tags', 'is_favorited', 'is_in_shopping_cart']

    def filter_tags(self, queryset, name, value):
        tags = self.request.query_params.getlist('tags', [])
        if tags:
            return queryset.filter(tags__slug__in=tags).distinct()
        return queryset

    def filter_favorites(self, queryset, name, value):
        if value:
            if not self.request.user.is_authenticated:
                return queryset.none()
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def filter_shopping_cart(self, queryset, name, value):
        if value:
            if not self.request.user.is_authenticated:
                return queryset.none()
            return queryset.filter(shopping_cart_items__user=self.request.user)
        return queryset
