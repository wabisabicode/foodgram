from django.shortcuts import get_object_or_404, redirect

from .models import RecipeShortURL


def redirect_from_short_url(request, hash):
    recipe_short_url = get_object_or_404(RecipeShortURL, hash=hash)
    recipe_detail_path = f'/recipes/{recipe_short_url.recipe.pk}/'
    recipe_full_url = request.build_absolute_uri(recipe_detail_path)

    return redirect(recipe_full_url)
