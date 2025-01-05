from django.urls import include, path
from rest_framework.routers import SimpleRouter

app_name = 'api'

router_v1 = SimpleRouter()
# makes /api/users/ and /api/users/{id}/:
router_v1.register('users', UsersViewSet, basename='users')

me_patterns = [
    path('', MeView.as_view(), name='user-me'),
    path('avatar/', AvatarView.as_view(), name='user-avatar'),
]

password_patterns = [
    path('', SetPasswordView.as_view(), name='user-set-password'),
]

auth_patterns = [
    path('login/', TokenLoginView.as_view(), name='token-login'),
    path('logout/', TokenLogoutView.as_view(), name='token-logout'),
]

urlpatterns = [
    path('', include(router_v1.urls)),
    path('users/me/', include(me_patterns)),
    path('users/set_password/', include(password_patterns)),
    path('auth/token/', include(password_patterns)),
]
