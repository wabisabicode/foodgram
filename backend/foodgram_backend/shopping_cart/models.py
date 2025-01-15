from django.contrib.auth import get_user_model
from django.db import models

from recipe.models import Recipe

User = get_user_model()


# class ShoppingCart(models.Model):
#     name = models.CharField(max_length=50, verbose_name='Название')
#     user = models.ForeignKey(User, verbose_name='Пользователь', on_delete=models.CASCADE)

#     class Meta:
#         verbose_name = 'Корзина покупок'
#         verbose_name_plural = 'Корзины покупок'

#     def __str__(self):
#         return self.name


class ShoppingCartItem(models.Model):
    # cart = models.ForeignKey(ShoppingCart, verbose_name='Корзина', on_delete=models.CASCADE)
    user = models.ForeignKey(User, verbose_name='Пользователь', on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, verbose_name='Рецепт', on_delete=models.CASCADE, related_name='shopping_cart_items')

    class Meta:
        verbose_name = 'Элемент в корзине'
        verbose_name_plural = 'Элементы в корзине'

    def __str__(self):
        return self.name
