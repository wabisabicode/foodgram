from django.contrib import admin
from django.contrib.auth.models import Group
from rest_framework.authtoken.models import TokenProxy

from .models import FGUser


class FGUserAdmin(admin.ModelAdmin):
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'avatar',
        'date_joined',
        'is_staff',
        'is_active',
        'is_superuser',
        'last_login'
    )
    search_fields = (
        'username',
        'email'
    )
    exclude = ('groups', 'user_permissions')


admin.site.register(FGUser, FGUserAdmin)
admin.site.unregister(Group)
admin.site.unregister(TokenProxy)
