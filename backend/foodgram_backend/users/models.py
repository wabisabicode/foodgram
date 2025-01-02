from django.contrib.auth.models import AbstractUser
from django.db import models


class FGUser(AbstractUser):
    email = models.EmailField(max_length=254, required=True)
    first_name = models.CharField(max_length=150, required=True)
    last_name = models.CharField(max_length=150, required=True)

    username = models.CharField(unique=True, max_length=150)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username
