from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from common.constants import EMAIL_MAX_LENGTH, NAME_MAX_LENGTH


class FGUser(AbstractUser):
    email = models.EmailField(
        verbose_name='Имейл',
        max_length=EMAIL_MAX_LENGTH,
        blank=False,
        unique=True
    )
    first_name = models.CharField(
        verbose_name='Имя', max_length=NAME_MAX_LENGTH, blank=False)
    last_name = models.CharField(
        verbose_name='Фамилия', max_length=NAME_MAX_LENGTH, blank=False)

    username = models.CharField(
        verbose_name='Имя пользователя',
        unique=True,
        max_length=NAME_MAX_LENGTH,
        validators=[RegexValidator(regex=r'^[\w.@+-]+\Z')])

    avatar = models.ImageField(
        verbose_name='Аватар', upload_to='users/avatars', default='')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

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
                name='users_no_selffollow'
            )
        ]
