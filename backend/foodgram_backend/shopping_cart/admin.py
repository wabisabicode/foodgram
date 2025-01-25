from django.contrib import admin

from .models import ShoppingCartItem


class ShoppingCartItemAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'user')


admin.site.register(ShoppingCartItem, ShoppingCartItemAdmin)
