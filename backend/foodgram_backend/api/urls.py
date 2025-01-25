from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import (AvatarView, IngredientListRetrieveViewSet, RecipeViewSet,
                    SetPasswordView, TagListRetrieveViewSet, UserViewSet,
                    download_shopping_cart)

app_name = 'api'

router_v1 = SimpleRouter()
router_v1.register('users', UserViewSet, basename='users')
router_v1.register('tags', TagListRetrieveViewSet, basename='tags')
router_v1.register(
    'ingredients', IngredientListRetrieveViewSet, basename='ingredients')
router_v1.register('recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('users/me/avatar/', AvatarView.as_view(), name='users-avatar'),
    path('users/set_password/',
         SetPasswordView.as_view(), name='set-password'),
    path('auth/', include('djoser.urls.authtoken')),
    path('recipes/download_shopping_cart/',
         download_shopping_cart, name='download-shopping-cart'),
    path('', include(router_v1.urls)),
]
