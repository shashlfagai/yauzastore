from django.shortcuts import render, get_object_or_404, redirect
from orders.views import get_user_order
from django.contrib import messages
from .models import StockBanner, Product, Category, ProductSize
from django.views.generic import DetailView
from django.db.models import OuterRef, Subquery, Sum, IntegerField
from django.db.models.functions import Coalesce
from .forms import AddToCartForm
from orders.models import OrderItem
from django.utils import timezone
from django.core.paginator import Paginator


def index(request):
    banners = StockBanner.objects.all().order_by('serial_number')
    promo_banners = []
    for banner in banners:
        promo_banners.append(banner.image.url)
    first_banner = promo_banners[0]
    next_bunners = promo_banners[1:]
    # Фильтрация товаров по количеству
    product_sizes = ProductSize.objects.filter(
        product=OuterRef('pk')
    ).values('product').annotate(
        total_quantity=Coalesce(Sum('quantity'), 0)
    ).values('total_quantity')

    products = Product.objects.annotate(
        total_quantity=Subquery(product_sizes, output_field=IntegerField())
    ).filter(
        total_quantity__gt=0
    ).prefetch_related(
        'categories'
    ).order_by(
        '-created_at'
    )
    # Разделяем товары по категориям
    products_by_category = {}
    for product in products:
        # Если у товара несколько категорий, выбираем первую для упрощения
        first_category = product.categories.first()
        if first_category:
            if first_category not in products_by_category:
                products_by_category[first_category] = []
            products_by_category[first_category].append(product)
    # Список товаров для чередования
    interleaved_products = []
    # Чередуем товары по категориям, пока есть товары
    while any(products_by_category.values()):
        for category_products in products_by_category.values():
            if category_products:
                interleaved_products.append(category_products.pop(0))
    # Пагинация
    paginator = Paginator(interleaved_products, 8)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    context = {
        'first_banner': first_banner,
        'next_banners': next_bunners,
        'page_obj': page_obj
    }
    return render(request, 'shop/index.html', context)


def about(request):
    return render(request, 'shop/about.html')


def wear(request):
    category = Category.objects.get(id=4)
    subcategories = category.subcategories.all()
    category_id = category.id
    subcategory_id = request.GET.get('subcategory_id')
    product_sizes = ProductSize.objects.filter(
        product=OuterRef('pk')
    ).values('product').annotate(
        total_quantity=Coalesce(Sum('quantity'), 0)
    ).values('total_quantity')
    products = Product.objects.filter(categories=category_id)
    if subcategory_id:
        products = products.filter(subcategories__id=subcategory_id)
    products = products.annotate(
        total_quantity=Subquery(product_sizes, output_field=IntegerField())
    ).filter(total_quantity__gt=0)
    # Пагинация
    paginator = Paginator(products, 8)  # 10 товаров на странице
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    return render(
        request,
        'shop/products.html',
        {
            'products': page_obj,
            'subcategories': subcategories,
            'current_view': 'wear'
        }
    )


def accessories(request):
    category = Category.objects.get(id=5)
    subcategories = category.subcategories.all()
    subcategory_id = request.GET.get('subcategory_id')
    category_id = category.id
    product_sizes = ProductSize.objects.filter(
        product=OuterRef('pk')
    ).values('product').annotate(
        total_quantity=Coalesce(Sum('quantity'), 0)
    ).values('total_quantity')
    products = Product.objects.filter(categories=category_id)
    if subcategory_id:
        products = products.filter(subcategories__id=subcategory_id)
    products = products.annotate(
        total_quantity=Subquery(product_sizes, output_field=IntegerField())
    ).filter(total_quantity__gt=0)
    paginator = Paginator(products, 8)  # 10 товаров на странице
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    return render(
        request,
        'shop/products.html',
        {
            'products': page_obj,
            'subcategories': subcategories,
            'current_view': 'accessories'
        }
    )


class ItemsDetailView(DetailView):
    model = Product
    template_name = 'shop/item_page.html'
    context_object_name = 'item'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        sizes = product.sizes.filter(quantity__gt=0)
        total_quantity = sum(size.quantity for size in sizes)
        form = AddToCartForm(product=product)
        context['sizes'] = sizes
        context['total_quantity'] = total_quantity
        context['form'] = form
        return context


def add_to_order(request, pk):
    product = get_object_or_404(Product, id=pk)
    if request.method == 'POST':
        form = AddToCartForm(request.POST, product=product)
        if form.is_valid():
            size = form.cleaned_data['size']
            quantity = 1  # Assuming quantity is fixed at 1 for simplicity
            if request.user.is_authenticated:
                # For authenticated users
                order = get_user_order(request.user)
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
                    order_item.quantity += quantity
                    order_item.save()
                messages.success(request, 'Товар добавлен в корзину!')
            else:
                # For unauthenticated users (using session-based cart)
                cart = request.session.get('cart', {})
                date_added = timezone.now()
                item_key = f"{product.id}-{size.id}"
                if item_key in cart:
                    cart[item_key]['quantity'] += quantity
                else:
                    image_url = product.images.first().image.url
                    cart[item_key] = {
                        'product_id': product.id,
                        'size_id': size.id,
                        'quantity': quantity,
                        'price': str(product.price.amount),
                        'image': str(image_url),
                        'discount_price': int(
                            product.get_discounted_price().amount
                        ),
                        'date_added': date_added.isoformat()
                    }
                request.session['cart'] = cart
                messages.success(request, 'Товар добавлен в корзину!')
            if product.categories.filter(name='Одежда').exists():
                return redirect('wear')
            elif product.categories.filter(name='Аксессуары').exists():
                return redirect('accessories')
    else:
        form = AddToCartForm(product=product)
    return render(
        request, 'shop/item_page.html',
        {'form': form, 'item': product}
    )


def get_session_order(request):
    cart = request.session.get('cart', {})
    return cart


def save_session_order(request, cart):
    request.session['cart'] = cart


def promo(request):
    subcategories = []
    discounted_products = [
        product for product in Product.objects.all() if product.has_discount()
    ]
    for product in discounted_products:
        product_subcategories = product.subcategories.all()
        for subcategory in product_subcategories:
            subcategories.append(subcategory)
        # Получаем выбранную подкатегорию из GET-параметров
    selected_subcategory_id = request.GET.get('subcategory_id')
    # Фильтруем продукты по выбранной подкатегории, если она задана
    if selected_subcategory_id:
        discounted_products = Product.objects.filter(
            id__in=[product.id for product in discounted_products],
            subcategories__id=selected_subcategory_id
        ).distinct()
    paginator = Paginator(discounted_products, 8)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    context = {
        'products': page_obj,
        'subcategories': subcategories,
        'current_view': 'promo'
    }
    return render(request, 'shop/promo.html', context)


def privacy_policy(request):
    return render(request, 'shop/privacy_policy.html')


def refund_and_exchange_policy(request):
    return render(request, 'shop/refund_and_exchange_policy.html')
