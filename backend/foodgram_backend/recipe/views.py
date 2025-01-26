from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect

from .models import RecipeShortURL


def redirect_from_short_url(request, hash):
    recipe_short_url = get_object_or_404(RecipeShortURL, hash=hash)
    return redirect(
        'frontend-recipe-detail',
        kwargs={'pk': recipe_short_url.recipe.pk}
    )


def placeholder_view(request, pk):
    return HttpResponse(
        f'This route is handled by the frontend. Recipe ID: {pk}'
    )
