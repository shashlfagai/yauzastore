from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
        )
    phone_number = models.CharField('Номер телефтона', max_length=20)
    email = models.EmailField('Email адрес')
    social_link = models.URLField(
        'Ссылка на социальную сеть',
        blank=True,
        null=True
        )
    agree_to_privacy_policy = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = "Информация о пользователе"
        verbose_name_plural = "Информания о пользователях"
