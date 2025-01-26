from django.shortcuts import get_object_or_404, redirect

from .models import RecipeShortURL


def redirect_from_short_url(request, hash):
    recipe_short_url = get_object_or_404(RecipeShortURL, hash=hash)
    return redirect('api:recipes-detail', pk=recipe_short_url.recipe.pk)
