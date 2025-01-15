from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import AvatarView, UserViewSet, MeView, SetPasswordView, TokenCreateView, TokenLogoutView
from .views import TagListRetrieveViewSet, IngredientListRetrieveViewSet, RecipeViewSet
from .views import MySubscriptions
from .views import download_shopping_cart

app_name = 'api'

router_v1 = SimpleRouter()
# makes /api/users/ and /api/users/{id}/:
router_v1.register('users', UserViewSet, basename='users')
router_v1.register('tags', TagListRetrieveViewSet, basename='tags')
router_v1.register(
    'ingredients', IngredientListRetrieveViewSet, basename='ingredients')
router_v1.register('recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('users/me/', MeView.as_view(), name='users-me'),
    path('users/me/avatar/', AvatarView.as_view(), name='users-avatar'),
    path('users/set_password/', SetPasswordView.as_view(), name='set-password'),
    path('users/subscriptions/', MySubscriptions.as_view(), name='my-subscriptions'),
    path('auth/token/login/', TokenCreateView.as_view(), name='token-login'),
    path('auth/token/logout/', TokenLogoutView.as_view(), name='token-logout'),
    path('recipes/download_shopping_cart/',
         download_shopping_cart, name='download-shopping-cart'),
    path('', include(router_v1.urls)),
]
