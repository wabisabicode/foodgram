from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from common.constants import EMAIL_MAX_LENGTH, NAME_MAX_LENGTH


class FGUser(AbstractUser):
    email = models.EmailField(max_length=EMAIL_MAX_LENGTH, blank=False)
    first_name = models.CharField(max_length=NAME_MAX_LENGTH, blank=False)
    last_name = models.CharField(max_length=NAME_MAX_LENGTH, blank=False)

    username = models.CharField(
        unique=True,
        max_length=NAME_MAX_LENGTH,
        validators=[RegexValidator(regex=r'^[\w.@+-]+\Z')])

    avatar = models.ImageField(upload_to='users/avatars', default='')

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
            models.UniqueConstraint(fields=['subscriber', 'creator'],
                                    name='unique_subscription'),
            models.CheckConstraint(check=~models.Q(
                subscriber=models.F('creator')),
                name='%(app_label)s_%(class)s_no_selffollow'
            )
        ]
