from django.contrib.auth.models import AbstractUser
from django.db import models


class FGUser(AbstractUser):
    email = models.EmailField(max_length=254, blank=False)
    first_name = models.CharField(max_length=150, blank=False)
    last_name = models.CharField(max_length=150, blank=False)

    username = models.CharField(unique=True, max_length=150)

    # is_subscribed = models.BooleanField()
    avatar = models.ImageField(upload_to='users/avatars')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username


class Subscription(models.Model):
    subscriber = models.ForeignKey(
        FGUser, related_name='following', on_delete=models.CASCADE)
    creator = models.ForeignKey(
        FGUser, related_name='subscribers', on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['subscriber', 'creator'],
                name='unique_subscription')
        ]
