from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .models import Order, OrderItem, PromoCode, BulkDiscount
from accounts.models import UserProfile
from .forms import PromoCodeForm
from shop.models import Product, ProductSize
from collections import defaultdict
from djmoney.money import Money
from decimal import InvalidOperation
from django.urls import reverse


def gather_discount_data(order_items):
    product_discount = defaultdict(int)
    category_item_count = defaultdict(int)
    subcategory_item_count = defaultdict(int)
    category_discount = defaultdict(int)
    subcategory_discount = defaultdict(int)

    for item in order_items:
        if isinstance(item, dict):
            product = get_object_or_404(Product, id=item['product_id'])
            for category in product.categories.all():
                category_item_count[category.id] += item['quantity']
            for subcategory in product.subcategories.all():
                subcategory_item_count[subcategory.id] += item['quantity']
        else:
            for category in item.product.categories.all():
                category_item_count[category.id] += item.quantity
            for subcategory in item.product.subcategories.all():
                subcategory_item_count[subcategory.id] += item.quantity
    # Применение скидок за количество
    for category_id, count in category_item_count.items():
        bulk_discounts = (
            BulkDiscount.objects.filter(
                categories__id=category_id
            ).order_by(
                '-minimum_quantity'
            )
        )
        for bulk_discount in bulk_discounts:
            if count >= bulk_discount.minimum_quantity:
                category_discount[category_id] = bulk_discount.discount_amount
                break
    # Применение скидок за количество по подкатегориям
    for subcategory_id, count in subcategory_item_count.items():
        bulk_discounts = (
            BulkDiscount.objects.filter(
                subcategories__id=subcategory_id
            ).order_by(
                '-minimum_quantity'
            )
        )
        for bulk_discount in bulk_discounts:
            if count >= bulk_discount.minimum_quantity:
                subcategory_discount[subcategory_id] = (
                    bulk_discount.discount_amount
                )
                break
    return (
        product_discount,
        category_item_count,
        category_discount,
        subcategory_item_count,
        subcategory_discount
    )


def apply_discount_to_items(
    order_items,
    product_discount,
    category_discount,
    subcategory_discount
):
    total_discount = 0
    for item in order_items:
        bulk_discount = Money(0, 'RUB')
        if isinstance(item, dict):
            procent_discount_price = item['discount_price']
            product = get_object_or_404(Product, id=item['product_id'])
            if product.id in product_discount:
                total_discount += (
                    product_discount[product.id] * item['quantity']
                )
            for category in product.categories.all():
                if category.id in category_discount:
                    bulk_discount = category_discount[category.id]
                    total_discount += bulk_discount * item['quantity']
            for subcategory in product.subcategories.all():
                if subcategory.id in subcategory_discount:
                    bulk_discount = subcategory_discount[subcategory.id]
                    total_discount += bulk_discount * item['quantity']
            price = item['price']
            if price == procent_discount_price:
                item['discount_price'] = (
                    int(
                        int(price) - bulk_discount.amount
                    )
                )
        else:
            if item.product.id in product_discount:
                total_discount += (
                    product_discount[item.product.id]
                    * item.quantity
                )
            for category in item.product.categories.all():
                if category.id in category_discount:
                    bulk_discount = category_discount[category.id]
                    total_discount += bulk_discount * item.quantity
            for subcategory in item.product.subcategories.all():
                if subcategory.id in subcategory_discount:
                    bulk_discount = subcategory_discount[subcategory.id]
                    total_discount += bulk_discount * item.quantity
            price = item.price
            item.discount_price = price.amount - bulk_discount.amount
    return total_discount


def apply_promotions(order_items, promo_code=None):
    # Собираем данные о скидках, включая категории и подкатегории
    (
        product_discount,
        category_item_count,
        category_discount,
        subcategory_item_count,
        subcategory_discount
    ) = gather_discount_data(order_items)

    # Применяем скидки на товары
    total_discount = apply_discount_to_items(
        order_items,
        product_discount,
        category_discount,
        subcategory_discount
    )
    procent_discount = 0
    for item in order_items:
        if isinstance(item, dict):
            if item['discount_price']:
                product = get_object_or_404(Product, id=item['product_id'])
                procent_discount += product.get_discount() * item['quantity']
        else:
            if item.discount_price:
                procent_discount += (
                    item.product.get_discount()
                    * item.quantity
                )
    total_discount += procent_discount
    # Вычисляем итоговую стоимость после всех примененных скидок
    total_cost = calculate_total_cost(order_items)
    total_discount_cost = total_cost - total_discount
    # Применение промокода
    if promo_code and promo_code.is_valid():
        promo_discount = total_discount_cost * (promo_code.discount / 100)
        total_discount += promo_discount

    return total_discount


@csrf_exempt
def update_order_quantity(request):
    if request.method == 'POST':
        operation = request.POST.get('operation')
        if request.user.is_authenticated:
            item_id = request.POST.get('item_id')
            order_item = get_object_or_404(OrderItem, id=item_id)
            if operation == 'increase':
                order_item.quantity += 1
            elif operation == 'decrease' and order_item.quantity > 1:
                order_item.quantity -= 1
            order_item.save()
            messages.success(request, 'Количество товара обновлено!')
        else:
            cart = request.session.get('cart', {})
            product_id = request.POST.get('product_id')
            size_id = request.POST.get('size_id')
            operation = request.POST.get('operation')
            item_id = f'{product_id}-{size_id}'
            if item_id in cart:
                if operation == 'increase':
                    cart[item_id]['quantity'] += 1
                elif (
                    operation == 'decrease'
                    and cart[item_id]['quantity'] > 1
                ):
                    cart[item_id]['quantity'] -= 1
            request.session['cart'] = cart
            messages.success(request, 'Количество товара обновлено!')
    return redirect('order_view')


def order_view(request):
    procent_discount = 0
    if request.user.is_authenticated:
        order = get_user_order(request.user)
        items = order.items.all().order_by('-date_added')
        promo_code = order.promo_code
    else:
        cart = request.session.get('cart', {})
        items = []
        promo_code = request.session.get('promo_code')
        for value in cart.values():
            product = get_object_or_404(Product, id=value['product_id'])
            size = get_object_or_404(ProductSize, id=value['size_id'])
            promotions = product.promotions.all()
            items.append({
                'product': product.name,
                'size': size.size,
                'size_id': value['size_id'],
                'quantity': value['quantity'],
                'price': value['price'],
                'product_id': value['product_id'],
                'image': value['image'],
                'promotions': promotions,
                'discount_price': value['discount_price'],
                'date_added': value.get('date_added')
            })
        items.sort(key=lambda x: x['date_added'], reverse=True)
    total_discount = apply_promotions(items, promo_code)
    total_cost = calculate_total_cost(items)
    total_discount_cost = total_cost - total_discount
    if promo_code:
        promo_code = str(promo_code.code)
    return render(
        request,
        'orders/order.html',
        {
            'items': items,
            'total_discount': total_discount,
            'total_cost': total_cost,
            'total_discount_cost': total_discount_cost,
            'promo_code': promo_code
        }
    )


def remove_from_order(request, item_id):
    if request.user.is_authenticated:
        order_item = get_object_or_404(
            OrderItem,
            id=item_id,
            order__user=request.user
        )
        order_item.delete()
        messages.success(request, 'Товар удален из корзины!')
        return redirect('order_view')
    else:
        cart = request.session.get('cart', {})
        key_for_del = []
        for key, value in cart.items():
            if item_id == value['product_id']:
                key_for_del.append(key)
        for key in key_for_del:
            del cart[key]
        save_session_order(request, cart)
        messages.success(request, 'Товар удален из корзины!')
        return redirect('order_view')


def calculate_total_cost(items):
    total_cost = Money(0, 'RUB')
    for item in items:
        if isinstance(item, dict):
            item_order = get_object_or_404(Product, id=item['product_id'])
            price = item_order.price
            quantity = item['quantity']
            try:
                total_cost += price * quantity
            except (InvalidOperation, ValueError) as e:
                print(f"Error converting price to Money: {price}, error: {e}")
        else:
            total_cost += item.price * item.quantity
    return total_cost


def apply_promo_code(request):
    if request.method == 'POST':
        form = PromoCodeForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            try:
                promo_code = PromoCode.objects.get(code=code, active=True)
                if not promo_code.is_valid():
                    messages.error(request, "Промокод недействителен.")
                elif Order.promo_code_used_by_user(promo_code, request.user):
                    messages.error(
                        request,
                        "Вы уже использовали этот промокод."
                    )
                else:
                    order = Order.objects.filter(
                        user=request.user,
                        status='pending'
                    ).first()
                    if order:
                        order.promo_code = promo_code
                        order.save()
                        messages.success(
                            request,
                            "Промокод успешно применён."
                        )
                    else:
                        messages.error(
                            request,
                            "Нет доступного заказа для применения промокода."
                        )
            except PromoCode.DoesNotExist:
                messages.error(request, "Неверный промокод.")
        else:
            messages.error(request, "Форма заполнена некорректно.")
    return redirect('order_view')


def making_order_view(request):
    if not request.user.is_authenticated:
        messages.error(
            request,
            'Чтобы оформить заказ, '
            'необходимо войти в систему или зарегистрироваться.'
        )
        return redirect(f'/accounts/register?next={request.path}')
    order = get_user_order(request.user)
    items = order.items.all().order_by('-date_added')
    promo_code = order.promo_code
    insufficient_stock = False
    for item in items:
        product = get_object_or_404(Product, id=item.product_id)
        size = get_object_or_404(ProductSize, product=product, id=item.size_id)

        if size.quantity < item.quantity:
            messages.error(
                request,
                f"Товара {product.name}"
                f" в размере {size.size}"
                f" доступно только {size.quantity} шт."
            )
            insufficient_stock = True

    if insufficient_stock:
        return redirect('order_view')
    total_discount = apply_promotions(items, promo_code)
    total_cost = calculate_total_cost(items)
    total_discount_cost = total_cost - total_discount
    if request.user.is_authenticated:
        order.update_total_price(total_cost, total_discount)
    return render(request, 'orders/making_order.html', {
        'items': items,
        'total_discount_cost': total_discount_cost,
        'total_cost': total_cost,
    })


def submit_order(request):
    if request.method == 'POST':
        # Получение заказа пользователя (предполагается, что он уже создан)
        order = get_user_order(request.user)

        # Получение выбранных значений из формы
        shipping_method = request.POST.get('shipping_method', 'pickup')
        payment_method = request.POST.get('payment_method', 'cash')

        # Установка выбранных методов и изменение статуса заказа
        order.delivery_method = shipping_method
        order.payment_method = payment_method
        order.status = 'processing'
        if not hasattr(order.user, 'profile'):
            UserProfile.objects.create(user=order.user)
        order.phone_number = order.user.profile.phone_number
        for item in order.items.all():
            if item.size.quantity < item.quantity:
                messages.error(
                    request,
                    f"Недостаточно товара {item.product.name} на складе."
                )
                return redirect('making_order_view')

            # Списание товара
            item.size.quantity -= item.quantity
            item.size.save()
        order.save()

        # Сообщение об успешной отправке
        messages.success(request, 'Ваш заказ был успешно отправлен! Вы можете забрать в нашем шоу-руме!')

        # Перенаправление на страницу с информацией о заказе
        return redirect(reverse('order_detail', args=[order.id]))

    # В случае GET-запроса перенаправление на страницу оформления заказа
    return redirect('making_order_view')


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/order_history.html', {'orders': orders})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})


def get_user_order(user):
    order, created = Order.objects.get_or_create(user=user, status='pending')
    return order


def save_session_order(request, cart):
    request.session['cart'] = cart
    request.session.modified = True
