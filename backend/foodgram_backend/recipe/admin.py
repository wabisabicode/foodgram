from django.contrib import admin

from .models import Ingredient, Recipe, Tag, Favorite

admin.site.register(Ingredient)
admin.site.register(Recipe)
admin.site.register(Tag)
admin.site.register(Favorite)