from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

from .constants import MIN_COOKING_TIME

User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField(max_length=50, verbose_name='Название')
    measurement_unit = models.CharField(
        max_length=50, verbose_name='Единицы измерения')

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=50, verbose_name='Название')
    slug = models.SlugField(max_length=50, unique=True, verbose_name='Слаг')

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    name = models.CharField(max_length=256, verbose_name='Название')
    image = models.ImageField(upload_to='recipes/images', verbose_name='Изображение')
    text = models.TextField(verbose_name='Текст')
    cooking_time = models.IntegerField(
        verbose_name='Время приготовления',
        validators=[MinValueValidator(MIN_COOKING_TIME)])
    author = models.SlugField()  # change to Foreign Key with FGUser
    # Looks like dynamic properties, i.e. to handle through Many-to-Many deps
    # is_favorited = models.ManyToManyField(
    #     User, through='RecipeIsFavorited', verbose_name='В избранном')

    # Through ShoppingCartItem and, possibly, ShoppingCart models
    # is_in_shopping_cart = models.ManyToManyField(
    #     User, through='RecipeIsInCart', verbose_name='В списке покупок')

    tags = models.ManyToManyField(
        Tag,
        through='RecipeTag',
        verbose_name='Тег'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиент'
    )

    pub_date = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата публикации')

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('pub_date',)

    def __str__(self):
        return self.name


class RecipeTag(models.Model):
    recipe = models.ForeignKey(
        'Recipe', verbose_name='Рецепт', on_delete=models.CASCADE)
    tag = models.ForeignKey(
        'Tag', verbose_name='Тег', on_delete=models.SET_NULL)

    class Meta:
        verbose_name = 'Связь рецепта и тега'
        verbose_name_plural = 'Связи рецепта и тега'


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        'Recipe', verbose_name='Рецепт', on_delete=models.CASCADE)
    ingredient = models.ForeignKey(
        'Ingredient', verbose_name='Ингредиент', on_delete=models.SET_NULL)

    class Meta:
        verbose_name = 'Связь рецепта и ингредиента'
        verbose_name_plural = 'Связи рецепта и ингредиента'
