from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import UserViewSet, MeViewSet

app_name = 'api'

router_v1 = SimpleRouter()
# makes /api/users/ and /api/users/{id}/:
router_v1.register('users', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router_v1.urls)),
    # path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('users/me/', MeViewSet, name='users-me'),
    # path('users/me/avatar/', AvatarView.as_view(), name='users-avatar'),
    # path('users/set_password/', SetPasswordView.as_view(),
    #      name='user-set-password'),
    # path('auth/token/login/', TokenLoginView.as_view(), name='token-login'),
    # path('auth/token/logout/', TokenLogoutView.as_view(), name='token-logout'),
]
