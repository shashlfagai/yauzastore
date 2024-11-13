from django.urls import path
from . import views

urlpatterns = [
    path('', views.account, name='account'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('edit/', views.edit_account, name='edit_account'),
    path('change-password/', views.change_password, name='change_password'),
    path('logout/', views.user_logout, name='logout')
]
