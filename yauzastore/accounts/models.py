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
    agree_to_offer = models.BooleanField(default=False)
    offer_agreed_at = models.DateTimeField(null=True, blank=True)


    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = "Информация о пользователе"
        verbose_name_plural = "Информания о пользователях"


class UserAgreement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    agreed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.user.first_name} {self.user.last_name}) — ознакомился и согласился с публичной офертой {self.agreed_at}"
    
    class Meta:
        verbose_name = "Публичная оферта"
        verbose_name_plural = "Публичная оферта"