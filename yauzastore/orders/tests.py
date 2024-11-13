from django.test import TestCase, Client
from django.contrib.auth.models import User
from shop.models import (
    Category,
    SubCategory,
    Size,
    Product,
    ProductImage,
    ProductSize,
    Promo
)
from .views import apply_promotions, calculate_total_cost
from orders.models import Order, OrderItem, PromoCode, BulkDiscount
from djmoney.money import Money
from django.utils import timezone


class OrderTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Создание тестового пользователя
        self.user = User.objects.create_user(
            username='testuser',
            password='password'
        )

        # Создание категорий и подкатегорий
        self.category = Category.objects.create(name='Wear')
        self.subcategory = SubCategory.objects.create(
            name='Clothes',
            parent_category=self.category
        )

        # Создание размеров
        self.size_small = Size.objects.create(name='Small')
        self.size_medium = Size.objects.create(name='Medium')

        # Создание товаров
        self.product1 = Product.objects.create(
            name='Test Shirt',
            description='A great shirt',
            price=Money(1000, 'RUB'),
            color='Blue',
            designer='John Doe'
        )
        self.product1.categories.add(self.category)
        self.product1.subcategories.add(self.subcategory)
        ProductImage.objects.create(
            product=self.product1,
            image='path/to/image.jpg'
        )

        self.product2 = Product.objects.create(
            name='Test Pants',
            description='A great pair of pants',
            price=Money(1500, 'RUB'),
            color='Black',
            designer='Jane Doe'
        )
        self.product2.categories.add(self.category)
        self.product2.subcategories.add(self.subcategory)
        ProductImage.objects.create(
            product=self.product2,
            image='path/to/image.jpg'
        )

        # Создание размера и элементов заказа
        self.size_small_obj = ProductSize.objects.create(
            product=self.product1,
            size=self.size_small,
            quantity=10
        )
        self.size_medium_obj = ProductSize.objects.create(
            product=self.product2,
            size=self.size_medium,
            quantity=5
        )

        # Создание заказа
        self.order = Order.objects.create(
            user=self.user,
            status='pending'
        )
        self.order_item1 = OrderItem.objects.create(
            order=self.order,
            product=self.product1,
            quantity=2,
            price=self.product1.price,
            size=self.size_small_obj
        )
        self.order_item2 = OrderItem.objects.create(
            order=self.order,
            product=self.product2,
            quantity=1,
            price=self.product2.price,
            size=self.size_small_obj
        )

        self.promo = Promo.objects.create(
            name='Summer Sale',
            discount_percentage=0
        )

        # Создание скидок
        self.bulk_discount = BulkDiscount.objects.create(
            promo=self.promo,
            discount_type=BulkDiscount.PRODUCT_BASED,
            discount_amount=200,
            minimum_quantity=2
        )
        self.bulk_discount.categories.add(self.category)

        # Создание промокодов
        self.promo_code = PromoCode.objects.create(
            promo=self.promo,
            code='SUMMER2024',
            discount=10.00,
            valid_from=timezone.now() - timezone.timedelta(days=1),
            valid_to=timezone.now() + timezone.timedelta(days=1),
            active=True
        )

    def tearDown(self):
        # Удаляем все созданные объекты
        self.promo_code.delete()
        self.bulk_discount.delete()
        self.order_item1.delete()
        self.order_item2.delete()
        self.order.delete()
        self.product1.delete()
        self.product2.delete()
        self.category.delete()
        self.subcategory.delete()
        self.size_small.delete()
        self.size_medium.delete()
        self.user.delete()

    def test_order_creation(self):
        """Тестируем создание заказа."""
        self.assertEqual(self.order.items.count(), 2)

    def test_apply_bulk_discount(self):
        """Тестируем применение скидки по количеству."""
        total_discount = apply_promotions(self.order.items.all())
        self.assertEqual(total_discount, Money(600, 'RUB'))

    def test_apply_promo_code(self):
        """Тестируем применение промокода."""
        self.order.promo_code = self.promo_code
        self.order.save()
        total_discount = apply_promotions(
            self.order.items.all(),
            self.promo_code
        )
        self.assertEqual(total_discount, Money(890, 'RUB'))

    def test_expired_promo_code(self):
        """Проверяем, что истекший промокод не применяется."""
        self.promo_code.valid_to = timezone.now() - timezone.timedelta(days=1)
        self.promo_code.save()
        total_discount = apply_promotions(
            self.order.items.all(),
            self.promo_code
            )
        self.assertEqual(total_discount, Money(600, 'RUB'))

    def test_inactive_promo_code(self):
        """Проверяем, что неактивный промокод не применяется."""
        self.promo_code.active = False
        self.promo_code.save()
        total_discount = apply_promotions(
            self.order.items.all(),
            self.promo_code
        )
        self.assertEqual(total_discount, Money(600, 'RUB'))

    def test_apply_discount_for_multiple_categories(self):
        """Проверяем применение скидок при пересечении категорий."""
        new_category = Category.objects.create(name='Footwear')
        self.product1.categories.add(new_category)
        bulk_discount_footwear = BulkDiscount.objects.create(
            promo=self.promo,
            discount_type=BulkDiscount.CATEGORY_BASED,
            discount_amount=150,
            minimum_quantity=1
        )
        bulk_discount_footwear.categories.add(new_category)
        total_discount = apply_promotions(self.order.items.all())
        self.assertEqual(total_discount, Money(900, 'RUB'))

    def test_calculate_total_cost_with_discounts(self):
        """Проверяем расчет итоговой стоимости с учетом всех скидок."""
        total_cost = calculate_total_cost(self.order.items.all())
        total_discount = apply_promotions(
            self.order.items.all(),
            self.promo_code
        )
        final_cost = total_cost - total_discount
        self.assertEqual(final_cost, Money(2610, 'RUB'))

    def test_guest_user_cart_session(self):
        """Тестируем сохранение корзины в сессии для гостевого пользователя."""
        session = self.client.session
        session['cart'] = {
            f'{self.product1.id}-{self.size_small.id}': {
                'product_id': self.product1.id,
                'quantity': 3,
                'size_id': self.size_small.id,
                'price': float(self.product1.price.amount),
                'image': 'path/to/image.jpg',
                'discount_price': 0
            }
        }
        session.save()

        response = self.client.get('/orders/')

        self.assertContains(response, 'Test Shirt')
        self.assertEqual(response.context['total_cost'], Money(3000, 'RUB'))
