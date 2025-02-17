from django.db import models
from shop.models import Product, Category, ProductSize, Promo, SubCategory
from django.contrib.auth.models import User
from djmoney.models.fields import MoneyField
from djmoney.money import Money
from django.utils import timezone
from yookassa import Payment


class PromoCode(models.Model):
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Код промокода"
    )
    promo = models.ForeignKey(
        Promo,
        on_delete=models.CASCADE,
        related_name='promo_codes'
    )
    discount = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Скидка (%)"
    )
    valid_from = models.DateTimeField(verbose_name="Действителен с")
    valid_to = models.DateTimeField(verbose_name="Действителен до")
    active = models.BooleanField(default=True, verbose_name="Активен")

    def is_valid(self):
        return (
            self.active
            and self.valid_from <= timezone.now() <= self.valid_to
        )


class BulkDiscount(models.Model):
    CATEGORY_BASED = 'CATEGORY_BASED'
    PRODUCT_BASED = 'PRODUCT_BASED'

    DISCOUNT_TYPES = [
        (CATEGORY_BASED, 'Скидка по категориям'),
        (PRODUCT_BASED, 'Скидка по количеству товаров')
    ]

    promo = models.ForeignKey(
        Promo, on_delete=models.CASCADE,
        related_name='bulk_discounts'
    )

    discount_type = models.CharField(
        "Тип скидки",
        max_length=20,
        choices=DISCOUNT_TYPES,
        default=PRODUCT_BASED
    )

    discount_amount = MoneyField(
        "Сумма скидки",
        max_digits=10,
        decimal_places=2,
        default_currency='RUB'
    )

    minimum_quantity = models.PositiveIntegerField(
        "Минимальное количество товаров"
    )

    categories = models.ManyToManyField(
        Category,
        related_name='bulk_discounts',
        verbose_name="Категории",
        blank=True
    )

    subcategories = models.ManyToManyField(
        SubCategory,
        related_name='bulk_discounts',
        verbose_name="Подкатегории",
        blank=True
    )

    products = models.ManyToManyField(
        Product,
        related_name='bulk_discounts',
        verbose_name="Товары",
        blank=True
    )

    def __str__(self):
        return (
            f"Bulk discount of {self.discount_amount} "
            f"for minimum {self.minimum_quantity} items"
        )

    class Meta:
        verbose_name = "Скидка за количество"
        verbose_name_plural = "Скидки за количество"


class Order(models.Model):

    DELIVERY_CHOICES = [
        ('standard', 'Стандартная доставка'),
        ('pickup', 'Самовывоз')
    ]

    PAYMENT_CHOICES = [
        ('cash', 'Оплата наличными или переводом при получении'),
        ('online', 'Онлайн-оплата')
    ]

    STATUS_CHOICES = [
        ('pending', 'В ожидании'),
        ('processing', 'В обработке'),
        ('shipped', 'Отправлено'),
        ('delivered', 'Доставлено в пункт выдачи'),
        ('canceled', 'Отменено'),
        ('done', 'Готов')
    ]

    delivery_method = models.CharField(
        max_length=20,
        choices=DELIVERY_CHOICES,
        default='standard',
        verbose_name="Способ доставки"
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_CHOICES,
        default='online',
        verbose_name="Способ оплаты"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Пользователь'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Статус"
    )

    total_price = MoneyField(
        max_digits=10,
        decimal_places=2,
        default_currency='RUB',
        default=Money(0, 'RUB'),
        verbose_name="Общая стоимость"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Создан"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Обновлен"
    )

    promo_code = models.ForeignKey(
        PromoCode,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="Промокод"
    )

    email = models.EmailField(
        null=True,
        blank=True
    )

    phone_number = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        verbose_name="Номер телефона"
    )

    # Delivery and payment information
    delivery_address = models.TextField(
        null=True,
        blank=True,
        verbose_name="Адрес доставки"
    )

    delivery_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    payment_status = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        default='pending',
        verbose_name="Статус оплаты"
    )

    delivery_status = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="Статус доставки"
    )

    def update_total_price(self, total_cost, total_discount):
        self.total_price = total_cost - total_discount
        self.save()

    def __str__(self):
        return f"Order {self.id} - {self.user or self.email}"

    def get_total_cost(self):
        return sum(item.quantity * item.price for item in self.items.all())

    def is_completed(self):
        """Check if the order is completed"""
        return self.status in ['delivered', 'canceled']

    def get_items(self):
        """Get all items in the order"""
        return self.items.all()

    @classmethod
    def promo_code_used_by_user(cls, promo_code, user):
        return cls.objects.filter(user=user, promo_code=promo_code).exists()

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Заказ'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='order_items',
        verbose_name="Товар"
    )
    size = models.ForeignKey(
        ProductSize,
        on_delete=models.CASCADE,
        verbose_name='Размер'
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="Количество"
    )
    price = MoneyField(
        max_digits=14,
        decimal_places=2,
        default_currency='RUB',
        verbose_name="Цена"
    )
    discount_price = MoneyField(
        max_digits=10,
        decimal_places=2,
        default_currency='RUB',
        null=True,
        blank=True,
        verbose_name="Цена со скидкой"
    )
    bulk_discount = MoneyField(
        max_digits=10,
        decimal_places=2,
        default_currency='RUB',
        null=True,
        blank=True,
        verbose_name="Скидка за колличество"
    )
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.product.name} in Order {self.order.id}'

    class Meta:
        verbose_name = "Товар в корзине"
        verbose_name_plural = "Товары в корзине"


class OrderTracking(models.Model):
    order = models.ForeignKey(
        Order,
        related_name='tracking',
        on_delete=models.CASCADE,
        verbose_name="Заказ"
    )
    status = models.CharField(
        max_length=20,
        choices=Order.STATUS_CHOICES,
        verbose_name="Статус"
    )
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Время")
    note = models.TextField(null=True, blank=True, verbose_name="Заметка")

    def __str__(self):
        return f"Order {self.order.id} - {self.status} at {self.timestamp}"

    class Meta:
        verbose_name = "Отслеживание заказа"
        verbose_name_plural = "Отслеживание заказов"


class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'В ожидании'),
        ('succeeded', 'Оплачен'),
        ('canceled', 'Отменен'),
    ]

    order = models.OneToOneField(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='payment'
    )
    payment_id = models.CharField(
        max_length=255,
        unique=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Payment {self.payment_id} - {self.status}"