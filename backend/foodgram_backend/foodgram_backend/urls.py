from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from recipe.views import placeholder_view, redirect_from_short_url

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls', namespace='api')),
    path('s/<str:hash>/', redirect_from_short_url,
         name='redirect-from-short-link'),
    path('recipes/<int:pk>/', placeholder_view, name='frontend-recipe-detail')
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
