from django_filters import rest_framework as filters

from recipe.models import Ingredient, Recipe, Tag


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(filters.FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug'
    )
    is_favorited = filters.BooleanFilter(
        method='filter_favorites')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('tags', 'is_favorited', 'is_in_shopping_cart', 'author')

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
