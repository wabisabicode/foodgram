from django.apps import AppConfig


class RecipeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'recipe'
    verbose_name = 'Приложение Рецепты'
