from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import UserProfile
from shop.models import Product, ProductSize, Size
from orders.models import OrderItem
from django.contrib.auth import get_user_model


User = get_user_model()


class AccountsTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            username='testuser',
            password='password'
            )

        # Создаем тестовый профиль
        self.profile = UserProfile.objects.create(
            user=self.user,
            phone_number='+1234567890'
            )

        # Создаем тестовый продукт и размер
        self.product = Product.objects.create(
            name='Test Product',
            price=1000
            )
        self.size = Size.objects.create(name='M')
        self.product_size = ProductSize.objects.create(
            product=self.product,
            size=self.size, quantity=5
            )

    def test_register_user(self):
        """Тестируем регистрацию нового пользователя без проверки редиректа."""
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'password1': 'testpassword123',
            'password2': 'testpassword123',
            'email': 'newuser@example.com',
            'first_name': 'First',
            'last_name': 'Last',
            'phone_number': '+1234567810',
            'social_link': 'http://example.com',
            'agree_to_privacy_policy': True
        })
        if response.status_code != 302:
            print(response.context['form'].errors)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_login_user(self):
        """Тестируем авторизацию пользователя."""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'password'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_save_cart_to_order(self):
        """Тестируем перенос товаров из корзины в заказ при регистрации."""
        session = self.client.session
        session['cart'] = {
            str(self.product.id): {
                'product_id': self.product.id,
                'quantity': 2,
                'size_id': self.product_size.id
            }
        }
        session.save()
        self.client.post(reverse('register'), {
            'username': 'newuser2',
            'password1': 'testpassword123',
            'password2': 'testpassword123',
            'email': 'newuser2@example.com',
            'first_name': 'First',
            'last_name': 'Last',
            'phone_number': '+1234567810',
            'social_link': 'http://example.com',
            'agree_to_privacy_policy': True
        })

        self.assertTrue(
            OrderItem.objects.filter(order__user__username='newuser2').exists()
            )

    def test_account_view(self):
        """Тестируем отображение страницы профиля пользователя."""
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('account'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.username)

    def test_edit_account(self):
        """Тестируем обновление данных пользователя и профиля."""
        self.client.login(username='testuser', password='password')
        self.client.post(reverse('edit_account'), {
            'username': self.user,
            'first_name': 'SuperFirstName',
            'last_name': 'NewLastName',
            'email': 'newemail@example.com',
            'phone_number': '+1987654321'
        })

        self.user.refresh_from_db()
        self.profile.refresh_from_db()
        self.assertEqual(self.user.first_name, 'SuperFirstName')
        self.assertEqual(self.user.last_name, 'NewLastName')
        self.assertEqual(self.user.email, 'newemail@example.com')
        self.assertEqual(self.profile.phone_number, '+1987654321')

    def test_change_password(self):
        """Тестируем изменение пароля пользователя."""
        self.client.login(username='testuser', password='password')
        response = self.client.post(reverse('change_password'), {
            'old_password': 'password',
            'new_password1': 'newpassword123',
            'new_password2': 'newpassword123'
        })

        self.assertEqual(response.status_code, 302)
        self.client.logout()
        login_response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'newpassword123'
        })
        self.assertEqual(login_response.status_code, 302)

    def test_logout_user(self):
        """Тестируем выход из системы."""
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            response.wsgi_request.user.is_authenticated
            )

    def test_user_login_with_cart(self):
        """Тестируем перенос корзины в заказ при авторизации."""
        session = self.client.session
        session['cart'] = {
            str(self.product.id): {
                'product_id': self.product.id,
                'quantity': 3,
                'size_id': self.product_size.id
            }
        }
        session.save()

        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'password'
        })
        self.assertEqual(response.status_code, 302)

        order_items = OrderItem.objects.filter(order__user=self.user)
        self.assertEqual(order_items.count(), 1)
        self.assertEqual(order_items.first().quantity, 3)
