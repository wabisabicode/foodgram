from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from common.constants import (INGR_NAME_MAX_LENGTH, INGR_UNIT_MAX_LENGTH,
                              MAX_COOKING_TIME, MAX_INGREDIENT_AMOUNT,
                              MIN_COOKING_TIME, MIN_INGREDIENT_AMOUNT,
                              RECIPE_NAME_MAX_LENGTH, SHORT_URL_MAX_LENGTH,
                              TAG_MAX_LENGTH)
from common.help_functions import generate_random_filename
from users.models import FGUser

User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField(
        max_length=INGR_NAME_MAX_LENGTH, verbose_name='Название')
    measurement_unit = models.CharField(
        max_length=INGR_UNIT_MAX_LENGTH, verbose_name='Единицы измерения')

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(
        max_length=TAG_MAX_LENGTH, verbose_name='Название')
    slug = models.SlugField(
        max_length=TAG_MAX_LENGTH, unique=True, verbose_name='Слаг')

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    name = models.CharField(
        max_length=RECIPE_NAME_MAX_LENGTH, verbose_name='Название')
    image = models.ImageField(
        upload_to='recipes/images', verbose_name='Изображение')
    text = models.TextField(verbose_name='Текст')

    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        validators=[
            MaxValueValidator(MAX_COOKING_TIME),
            MinValueValidator(MIN_COOKING_TIME)
        ]
    )
    author = models.ForeignKey(
        FGUser, verbose_name='Автор',
        on_delete=models.CASCADE
    )
    tags = models.ManyToManyField(Tag, verbose_name='Тег')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиент'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата публикации')

    class Meta:
        default_related_name = 'recipes'
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        'Recipe', verbose_name='Рецепт',
        on_delete=models.CASCADE
    )
    ingredient = models.ForeignKey(
        'Ingredient', verbose_name='Ингредиент', on_delete=models.CASCADE)
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество в рецепте',
        validators=[
            MaxValueValidator(MAX_INGREDIENT_AMOUNT),
            MinValueValidator(MIN_INGREDIENT_AMOUNT)
        ],
        default=1
    )

    class Meta:
        default_related_name = 'recipeingredients'
        verbose_name = 'Связь рецепта и ингредиента'
        verbose_name_plural = 'Связи рецепта и ингредиента'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient')
        ]

    def __str__(self):
        return self.ingredient.name


class RecipeShortURL(models.Model):
    recipe = models.ForeignKey(
        'Recipe', verbose_name='Рецепт', on_delete=models.CASCADE)
    hash = models.CharField(
        max_length=SHORT_URL_MAX_LENGTH, verbose_name='Хеш')

    def generate_hash(self):
        self.hash = generate_random_filename(length=8)
        self.save()


class Favorite(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='favorites')
    user = models.ForeignKey(FGUser, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite')
        ]
