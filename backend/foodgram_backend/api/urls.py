from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import UserViewSet, MeView, SetPasswordView, TokenCreateView, TokenLogoutView

app_name = 'api'

router_v1 = SimpleRouter()
# makes /api/users/ and /api/users/{id}/:
router_v1.register('users', UserViewSet, basename='users')

urlpatterns = [
    path('users/me/', MeView.as_view(), name='users-me'),
    # path('users/me/avatar/', AvatarView.as_view(), name='users-avatar'),
    path('users/set_password/', SetPasswordView.as_view(), name='set-password'),
    path('auth/token/login/', TokenCreateView.as_view(), name='token-login'),
    path('auth/token/logout/', TokenLogoutView.as_view(), name='token-logout'),
    path('', include(router_v1.urls)),
]
