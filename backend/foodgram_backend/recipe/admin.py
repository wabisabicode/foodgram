from django.contrib import admin

from .models import (Favorite, Ingredient, Recipe,
                     RecipeIngredient, RecipeShortURL, Tag)

RecipeTag = Recipe.tags.through


@admin.register(RecipeTag)
class TagsIntermediateAdmin(admin.ModelAdmin):
    list_display = ('id', 'custom_recipe', 'custom_tag')

    def custom_recipe(self, obj):
        return obj.recipe.name
    custom_recipe.short_description = 'рецепт'

    def custom_tag(self, obj):
        return obj.tag.name
    custom_tag.short_description = 'тег'


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 0


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'cooking_time_with_unit', 'author',
                    'favorites_count', 'tags_list', 'ingredients_list')
    readonly_fields = ('favorites_count',)
    search_fields = ('name', 'author', 'tags')
    list_filter = ('tags', 'author')

    inlines = (
        RecipeIngredientInline,
    )

    @admin.display(description='Добавлений в избранное',)
    def favorites_count(self, obj):
        return obj.favorites.count()

    def tags_list(self, obj):
        return ', '.join([tag.name for tag in obj.tags.all()])
    tags_list.short_description = 'Теги'

    def ingredients_list(self, obj):
        return ", ".join(
            [ri.ingredient.name for ri in obj.recipeingredients.all()]
        )
    ingredients_list.short_description = 'Ингредиенты'

    def cooking_time_with_unit(self, obj):
        return f'{obj.cooking_time}'
    cooking_time_with_unit.short_description = 'Время приготовления (мин)'

    # def save_model(self, request, obj, form, change):
    #     if not obj.recipeingredients.exists():
    #         raise ValidationError('Добавьте хотя бы один ингредиент')
    #     super().save_model(request, obj, form, change)


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


admin.site.register(Tag)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(RecipeShortURL, RecipeShortURLAdmin)
admin.site.register(RecipeIngredient, RecipeIngredientAdmin)
admin.site.register(Ingredient, IngredientAdmin)
