from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.forms import (
    UserCreationForm,
    UserChangeForm,
    PasswordChangeForm,
    AuthenticationForm
)
from django.core.exceptions import ValidationError
from .models import UserProfile


class CustomAuthenticationForm(AuthenticationForm):
    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        # Попытка аутентификации
        user = authenticate(
            request=self.request,
            username=username,
            password=password
            )
        if user is None:
            raise forms.ValidationError(
                "Неверное имя пользователя или пароль."
                )
        return cleaned_data


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone_number = forms.CharField(max_length=20, required=True)
    social_link = forms.URLField(required=False)
    agree_to_privacy_policy = forms.BooleanField(
        required=True,
        label="Я согласен на обработку персональных данных"
        )
    agree_to_offer = forms.BooleanField(
        required=True,
        label="Ознакомление с публичной офертой"
    )

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'password1',
            'password2',
            'phone_number',
            'social_link',
            'agree_to_privacy_policy',
            'agree_to_offer'
            ]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(UserRegisterForm, self).__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data.get('username').lower()
        if User.objects.filter(username=username).exists():
            if self.request:
                messages.success(
                    self.request,
                    'Пользователь с таким никнеймом уже существует.'
                    )
            raise ValidationError(
                'Пользователь с таким никнеймом уже существует.'
                )
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        if User.objects.filter(email=email).exists():
            if self.request:
                messages.success(
                    self.request,
                    'Пользователь с таким email уже существует.'
                    )
            raise ValidationError(
                'Пользователь с таким email уже существует.'
            )
        return email

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if UserProfile.objects.filter(phone_number=phone_number).exists():
            if self.request:
                messages.error(
                    self.request,
                    'Пользователь с таким номером телефона уже существует'
                    )
            raise ValidationError(
                'Пользователь с таким номером телефона уже существует.'
                )
        return phone_number

    def clean_agree_to_privacy_policy(self):
        agree_to_privacy_policy = self.cleaned_data.get(
            'agree_to_privacy_policy'
            )
        if not agree_to_privacy_policy:
            messages.error(
                self.request,
                'Вы должны согласиться на обработку персональных данных, '
                'чтобы зарегистрироваться.'
                )
            raise ValidationError(
                'Вы должны согласиться на обработку персональных данных,'
                ' чтобы зарегистрироваться.'
                )
        return agree_to_privacy_policy

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                phone_number=self.cleaned_data['phone_number'],
                social_link=self.cleaned_data['social_link'],
                agree_to_privacy_policy=self.cleaned_data[
                    'agree_to_privacy_policy'
                    ],
                agree_to_offer=self.cleaned_data[
                    'agree_to_offer'
                    ] 
            )
        return user


class UserUpdateForm(UserChangeForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']


class UserProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone_number', 'social_link']


class PasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label='Старый пароль',
        widget=forms.PasswordInput
        )
    new_password1 = forms.CharField(
        label='Новый пароль',
        widget=forms.PasswordInput
        )
    new_password2 = forms.CharField(
        label='Повторите новый пароль',
        widget=forms.PasswordInput
        )

    class Meta:
        model = User
        fields = ['old_password', 'new_password1', 'new_password2']
