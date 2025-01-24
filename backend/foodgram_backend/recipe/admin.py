from django.contrib import admin

from .models import Ingredient, Recipe, RecipeIngredient, Tag

admin.site.register(Tag)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 0


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'favorites_count')
    readonly_fields = ('favorites_count',)
    search_fields = ('name', 'author')
    list_filter = ('tags',)

    inlines = (
        RecipeIngredientInline,
    )


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    ordering = ('name',)


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
