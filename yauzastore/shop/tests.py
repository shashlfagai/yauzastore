from shop.models import (
    Category,
    SubCategory,
    Size,
    Product,
    ProductSize,
    Promo,
    ProductImage
)
from django.test import TestCase, Client
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from orders.models import OrderItem, Order, PromoCode
from django.contrib.auth.models import User
from djmoney.money import Money
import os


class ShopViewsTestCase(TestCase):

    def setUp(self):
        # Создаем тестовые данные
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='password'
        )
        # Создаем категории и подкатегории
        self.category = Category.objects.create(name='wear')
        self.subcategory = SubCategory.objects.create(
            name='Test SubCategory',
            parent_category=self.category
        )
        # Создаем размеры и товары
        self.size_small = Size.objects.create(name='Small')
        self.size_medium = Size.objects.create(name='Medium')
        self.product = Product.objects.create(
            name='Test Product',
            description='A great product',
            price=Money(10000, 'RUB'),
            color='Red',
            designer='John Doe'
        )
        self.product.categories.add(self.category)
        self.product.subcategories.add(self.subcategory)
        self.product_size_small = ProductSize.objects.create(
            product=self.product,
            size=self.size_small,
            quantity=10
        )
        self.product_size_medium = ProductSize.objects.create(
            product=self.product,
            size=self.size_medium,
            quantity=5
        )
        # Создаем изображения
        self.product_image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'',
            content_type='image/jpeg'
        )
        ProductImage.objects.create(
            product=self.product,
            image=self.product_image
        )
        # Создаем промо-акции
        self.promo = Promo.objects.create(
            name='Summer Sale',
            discount_percentage=15
        )
        self.promo.products.add(self.product)
        # Создаем промокод
        self.promo_code = PromoCode.objects.create(
            code='SUMMER2024',
            promo=self.promo,
            discount=15.00,
            valid_from=timezone.now() - timezone.timedelta(days=1),
            valid_to=timezone.now() + timezone.timedelta(days=30)
        )

    def tearDown(self):
        # Очистка созданных моделей
        PromoCode.objects.all().delete()
        Promo.objects.all().delete()
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        ProductSize.objects.all().delete()
        Product.objects.all().delete()
        Size.objects.all().delete()
        SubCategory.objects.all().delete()
        Category.objects.all().delete()
        User.objects.all().delete()
        for product_image in ProductImage.objects.all():
            os.remove(product_image.image.path)

    def test_items_detail_view(self):
        response = self.client.get(
            reverse('item-page', args=[self.product.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)
        self.assertContains(response, self.product.price)
        self.assertContains(response, self.size_small.name)
        self.assertContains(response, self.size_medium.name)

    def test_add_to_cart_authenticated_user(self):
        self.client.login(username='testuser', password='password')
        response = self.client.post(
            reverse('add_to_order', args=[self.product.id]),
            {'size': self.size_small.id}
        )
        self.assertEqual(response.status_code, 200)
        order = Order.objects.get(user=self.user)
        order_item = OrderItem.objects.get(
            order=order,
            product=self.product,
            size=self.product_size_small
        )
        self.assertEqual(order_item.quantity, 1)
        self.assertEqual(order_item.price, self.product.price)

    def test_add_to_cart_unauthenticated_user(self):
        response = self.client.post(reverse(
            'add_to_order', args=[self.product.id]),
            {'size': self.size_small.id}
        )
        self.assertEqual(response.status_code, 200)
        cart = self.client.session.get('cart', {})
        item_key = f"{self.product.id}-{self.size_small.id}"
        self.assertIn(item_key, cart)
        self.assertEqual(cart[item_key]['quantity'], 1)

    def test_promo_creation_valid(self):
        # Создаем валидную промо-акцию
        self.promo.categories.add(self.category)
        self.promo.products.add(self.product)
        # Проверяем, что промо-акция создана
        self.assertEqual(Promo.objects.count(), 1)
        created_promo = Promo.objects.first()
        self.assertEqual(created_promo.name, 'Summer Sale')
        self.assertEqual(created_promo.discount_percentage, 15.00)
        self.assertIn(self.category, created_promo.categories.all())
        self.assertIn(self.product, created_promo.products.all())

    def test_promo_creation_without_discount(self):
        # Пытаемся создать акцию без указания процента скидки
        promo = Promo(name='No Discount Promo')
        with self.assertRaises(ValidationError) as context:
            promo.full_clean()  # Вызовет проверку валидности
        self.assertIn(
            'Discount percentage is required for percentage discount.',
            context.exception.messages
        )

    def test_promo_str(self):
        # Проверяем строковое представление промо-акции
        promo = Promo.objects.create(
            name='Holiday Sale',
            discount_percentage=20.00
        )
        self.assertEqual(str(promo), 'Holiday Sale')

    def test_promo_with_categories_and_products(self):
        # Создаем промо-акцию с категориями и продуктами
        promo = Promo.objects.create(
            name='Spring Sale',
            discount_percentage=10.00
        )
        promo.categories.add(self.category)
        promo.products.add(self.product)

        # Проверяем связи
        self.assertIn(self.category, promo.categories.all())
        self.assertIn(self.product, promo.products.all())
