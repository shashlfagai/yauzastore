from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import (
    UserRegisterForm,
    UserUpdateForm,
    UserProfileUpdateForm,
    PasswordChangeForm,
    CustomAuthenticationForm
    )
from django.contrib.auth.decorators import login_required
from .models import UserProfile
from django.contrib.auth import (
    update_session_auth_hash,
    logout,
    authenticate,
    login
    )
from orders.views import get_user_order
from orders.models import OrderItem
from shop.models import Product, ProductSize


def register(request):
    cart = request.session.get('cart', {})
    if request.method == 'POST':
        form = UserRegisterForm(request.POST, request=request)
        if form.is_valid():
            user = form.save()
            form.cleaned_data.get('username')
            login(request, user)
            if cart:
                save_cart_to_order(user, cart)
            next_url = request.GET.get('next', 'home')
            messages.success(
                request, 'Теперь ты в нашей команде!'
                )
            return redirect(next_url)
    else:
        form = UserRegisterForm(request=request)
    return render(request, 'accounts/register.html', {'form': form})


def user_login(request):
    cart = request.session.get('cart', {})
    if request.method == 'POST':
        form = CustomAuthenticationForm(data=request.POST)
        username = request.POST.get('username').lower()
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if cart:
                save_cart_to_order(user, cart)
            messages.success(request, 'Вы успешно вошли в систему!')
            return redirect('home')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль.')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


def save_cart_to_order(user, cart):
    order = get_user_order(user)
    for item in cart.values():

        product = get_object_or_404(Product, id=item['product_id'])
        size = get_object_or_404(ProductSize, id=item['size_id'])
        quantity = item['quantity']
        order_item, created = OrderItem.objects.get_or_create(
            order=order,
            product=product,
            size=size,
            defaults={
                'quantity': quantity,
                'price': product.price,
                'discount_price': product.get_discounted_price
                }
        )

        if not created:
            order_item.quantity += item['quantity']
            order_item.save()


@login_required
def account(request):
    user = request.user
    try:
        user_profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        user_profile = None

    context = {
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'phone_number': (
            user_profile.phone_number
            if user_profile and user_profile.phone_number
            else 'Не указано'
        ),
        'social_link': (
            user_profile.social_link
            if user_profile and user_profile.social_link
            else 'Не указано'
        ),
    }
    return render(request, 'accounts/account.html', context)


@login_required
def edit_account(request):
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = UserProfileUpdateForm(
            request.POST,
            instance=request.user.profile
            )
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Ваш профиль был успешно обновлен!')
            return redirect('account')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = UserProfileUpdateForm(instance=request.user.profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form
    }
    return render(request, 'accounts/edit.html', context)


@login_required
def change_password(request):
    if request.method == 'POST':
        password_form = PasswordChangeForm(
            user=request.user,
            data=request.POST
            )
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Ваш пароль был успешно изменен!')
            return redirect('account')
    else:
        password_form = PasswordChangeForm(user=request.user)

    context = {
        'password_form': password_form,
    }
    return render(request, 'accounts/change_password.html', context)


def user_logout(request):
    logout(request)
    return redirect('home')
