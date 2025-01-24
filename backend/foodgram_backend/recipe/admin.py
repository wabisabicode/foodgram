from django.contrib import admin
from django.core.exceptions import ValidationError

from .models import Ingredient, Recipe, RecipeIngredient, Tag

tags_intermedate_model = Recipe.tags.through


@admin.register(tags_intermedate_model)
class TagsIntermediateAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'tag')


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

    def save_model(self, request, obj, form, change):
        if not obj.recipeingredients.exists():
            raise ValidationError('Добавьте хотя бы один ингредиент')
        super().save_model(request, obj, form, change)


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    ordering = ('name',)


admin.site.register(Tag)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
