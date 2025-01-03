from django.contrib.auth.models import AbstractUser
from django.db import models


class FGUser(AbstractUser):
    email = models.EmailField(max_length=254)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)

    username = models.CharField(unique=True, max_length=150)

    is_subscribed = models.BooleanField()
    avatar = models.ImageField(upload_to='users/avatars')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username
