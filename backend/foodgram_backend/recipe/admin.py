from django.contrib import admin

from .models import Ingredient, Recipe, RecipeIngredient, Tag

tags_intermedate_model = Recipe.tags.through


@admin.register(tags_intermedate_model)
class TagsIntermediateAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'tag')


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 0


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'cooking_time', 'author',
                    'favorites_count', 'tags_list')
    readonly_fields = ('favorites_count',)
    search_fields = ('name', 'author')
    list_filter = ('tags',)

    inlines = (
        RecipeIngredientInline,
    )

    @admin.display(description='Добавлений в избранное',)
    def favorites_count(self, obj):
        return obj.favorites.count()

    def tags_list(self, obj):
        return ', '.join([tag.name for tag in obj.tags.all()])
    tags_list.short_description = 'Теги'


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    ordering = ('name',)


admin.site.register(Tag)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
