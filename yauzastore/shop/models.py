from django.db import models
from django.utils.timezone import now
from djmoney.models.fields import MoneyField
from django.core.exceptions import ValidationError


class Category(models.Model):
    name = models.CharField('Название категории', max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"


class SubCategory(models.Model):
    name = models.CharField(
        'Название подкатегории',
        max_length=100
    )
    parent_category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='subcategories'
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Подкатегория"
        verbose_name_plural = "Подкатегории"


class Size(models.Model):
    name = models.CharField('Наименование размера', max_length=20)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Размер товара'
        verbose_name_plural = 'Размеры товара'


class ProductSize(models.Model):
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='sizes'
    )
    size = models.ForeignKey(
        Size,
        on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField('Количество')

    def __str__(self):
        return self.size.name

    class Meta:
        verbose_name = 'Размер товара для продукта'
        verbose_name_plural = 'Размеры товара для продуктов'


class Product(models.Model):
    name = models.CharField(
        'Название товара',
        max_length=255
    )
    description = models.TextField(
        'Описание товара (необязательное поле)',
        blank=True,
        null=True
    )
    price = MoneyField(
        'Цена товара',
        max_digits=14,
        decimal_places=2,
        default_currency='RUB'
    )
    categories = models.ManyToManyField(
        Category,
        related_name='products',
        verbose_name='Категории товара'
    )
    subcategories = models.ManyToManyField(
        SubCategory,
        related_name='products',
        verbose_name='Подкатегории товара',
        blank=True
    )
    created_at = models.DateTimeField(
        'Дата и время добавления',
        default=now
    )
    color = models.CharField(
        'Цвет товара',
        max_length=50,
        blank=True,
        null=True
    )
    designer = models.CharField(
        'Дизайнер товара',
        max_length=255,
        blank=True,
        null=True
    )

    def get_first_image(self):
        if self.images.exists():
            return self.images.first().image.url
        return None

    def get_discounted_price(self):
        best_discount = 0
        for promo in self.promotions.all():
            if promo.discount_percentage > best_discount:
                best_discount = promo.discount_percentage
        if best_discount:
            return round(self.price - (self.price * best_discount / 100))
        return self.price

    def get_discount(self):
        best_discount = 0
        for promo in self.promotions.all():
            if promo.discount_percentage > best_discount:
                best_discount = promo.discount_percentage
        if best_discount:
            return (self.price * best_discount / 100)
        return 0

    def has_discount(self):
        return self.promotions.exists()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"


class Promo(models.Model):

    name = models.CharField(
        "Название акции",
        max_length=100
        )
    discount_percentage = models.DecimalField(
        "Процент скидки",
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    categories = models.ManyToManyField(
        Category,
        related_name='promotions',
        verbose_name="Категория",
        blank=True
    )
    products = models.ManyToManyField(
        'Product',
        related_name='promotions',
        verbose_name="Товары",
        blank=True
    )

    def clean(self):
        if self.discount_percentage is None:
            raise ValidationError(
                'Discount percentage is required for percentage discount.'
            )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Акция"
        verbose_name_plural = "Акции"


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField('Изображение товара', upload_to='products/')

    def __str__(self):
        return f"{self.product.name} Image"

    class Meta:
        verbose_name = "Изображение товара"
        verbose_name_plural = "Изображения товара"


class StockBanner(models.Model):
    image = models.ImageField(
        'Изображение товара',
        upload_to='shop/img/homepage'
    )
    title = models.CharField(
        "Название акции",
        max_length=100,
        blank=True
    )
    description = models.TextField(
        "Описание акции",
        blank=True
    )
    created_at = models.DateTimeField(
        'Дата и время добавления',
        default=now
    )
    serial_number = models.CharField(
        'Порядковый номер акции',
        max_length=10,
        unique=True,
        blank=True,
        null=True
    )

    def __str__(self):
        return self.title if self.title else "Nothing in stock"

    class Meta:
        verbose_name = "Баннер акции"
        verbose_name_plural = "Баннер акций"


from django.db import models

class PartnerProjects(models.Model):
    FORM_TYPES = [
        ('realization', 'Сдача товаров на реализацию'),
        ('rental', 'Аренда места в шоуруме'),
        ('other', 'Другие предложения'),
    ]
    STATUS_CHOICES = [
        ('pending', 'В обработке'),
        ('approved', 'Одобрено'),
        ('rejected', 'Отказ'),
    ]
    form_type = models.CharField(
        max_length=20,
        choices=FORM_TYPES,
        verbose_name='Форма'
    )
    first_name = models.CharField(max_length=100, verbose_name='Имя')
    phone = models.CharField(max_length=20, verbose_name='Номер телефона')
    contact_preference = models.CharField(
        max_length=20,
        choices=[
            ('phone', 'По телефону'),
            ('telegram', 'Telegram'),
            ('whatsapp', 'WhatsApp'),
        ],
        verbose_name='Предпочтительный способ связи'
    )
    product_description = models.TextField(verbose_name='Описание проекта')
    project_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='Название проекта'
    )
    product_link = models.URLField(
        null=True,
        blank=True,
        verbose_name='Ссылка на примеры изделий/товаров'
    )
    social_link = models.URLField(verbose_name='Ссылка на соц. сети')
    additional_info = models.TextField(
        null=True, blank=True, verbose_name='Дополнительная информация'
    )
    shelf_preference = models.CharField(
        max_length=50,
        choices=[
            ('eye_level', 'Полка на уровне глаз'),
            ('below_eye', 'Полка чуть ниже уровня глаз'),
            ('any', 'Любая полка'),
        ],
        null=True, blank=True, verbose_name='Предпочтительная полка'
    )
    equipment_preference = models.CharField(
        max_length=20,
        choices=[
            ('table', 'Стол'),
            ('rail', 'Рэйл'),
            ('other', "Другое")
        ],
        null=True, blank=True, verbose_name='Оборудование'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус заявки'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата подачи'
    )
    agree_to_privacy_policy = models.BooleanField(
        default=False,
        verbose_name='Согласен с политикой конфиданциальности'
        )

    def __str__(self):
        return f"{self.get_form_type_display()} - {self.project_name} {self.first_name} ({self.phone}) {self.get_status_display()}"

    class Meta:
        verbose_name = 'Заявка на партнерство'
        verbose_name_plural = 'Заявки на партнерство'