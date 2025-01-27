from django.contrib import admin

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     RecipeShortURL, ShoppingCartItem, Tag)

RecipeTag = Recipe.tags.through


@admin.register(RecipeTag)
class TagsIntermediateAdmin(admin.ModelAdmin):
    list_display = ('id', 'custom_recipe', 'custom_tag')

    @admin.display(description='рецепт')
    def custom_recipe(self, obj):
        return obj.recipe.name

    @admin.display(description='тег')
    def custom_tag(self, obj):
        return obj.tag.name


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'cooking_time_with_unit', 'author',
                    'favorites_count', 'tags_list', 'ingredients_list')
    readonly_fields = ('favorites_count',)
    search_fields = ('name', 'author__username', 'tags__name')
    list_filter = ('tags', 'author')

    inlines = (
        RecipeIngredientInline,
    )

    @admin.display(description='Добавлений в избранное',)
    def favorites_count(self, obj):
        return obj.favorites.count()

    @admin.display(description='Теги')
    def tags_list(self, obj):
        return ', '.join(obj.tags.values_list('name', flat=True))

    @admin.display(description='Ингредиенты')
    def ingredients_list(self, obj):
        return ', '.join(
            obj.recipeingredients.values_list('ingredient__name', flat=True)
        )

    @admin.display(description='Время приготовления (мин)')
    def cooking_time_with_unit(self, obj):
        return f'{obj.cooking_time}'


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name', 'measurement_unit')
    list_filter = ('measurement_unit',)
    ordering = ('name',)


class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')


class RecipeShortURLAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'hash')


class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'user')


class ShoppingCartItemAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'user')


admin.site.register(Tag)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(RecipeShortURL, RecipeShortURLAdmin)
admin.site.register(RecipeIngredient, RecipeIngredientAdmin)
admin.site.register(ShoppingCartItem, ShoppingCartItemAdmin)
admin.site.register(Ingredient, IngredientAdmin)
