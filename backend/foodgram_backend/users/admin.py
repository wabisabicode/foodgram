from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from rest_framework.authtoken.models import TokenProxy

from .models import FGUser


class FGUserAdmin(UserAdmin):
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
        'last_login',
    )
    search_fields = (
        'username',
        'email'
    )
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )


admin.site.register(FGUser, FGUserAdmin)
admin.site.unregister(Group)
admin.site.unregister(TokenProxy)
