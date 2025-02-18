from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = (
        'product',
        'size',
        'quantity',
        'price',
        'discount_price',
        'bulk_discount',
        'date_added'
    )


class OrderAdmin(admin.ModelAdmin):
    readonly_fields = (
        'user',
    )

    list_display = (
        'id',
        'user',
        'phone_number',
        'status',
        'total_price',
        'created_at',
        'display_order_items'
    )

    list_filter = (
        'status',
        'created_at',
        'delivery_method',
        'payment_method'
    )

    inlines = [OrderItemInline]
    
    def get_queryset(self, request):
        """Фильтруем заказы в админке, исключая pending."""
        qs = super().get_queryset(request)
        return qs.exclude(status='pending')

    def display_order_items(self, obj):
        order_items = obj.items.all()
        items_info = []
        for item in order_items:
            size_name = item.size.size.name
            items_info.append(
                f"{item.product.name} ({size_name}) x {item.quantity}"
            )
        return ", ".join(items_info)
    display_order_items.short_description = 'Товары'


class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount', 'valid_from', 'valid_to', 'active']
    search_fields = ['code']
    list_filter = ['active', 'valid_from', 'valid_to']
    date_hierarchy = 'valid_from'


class BulkDiscountAdmin(admin.ModelAdmin):
    list_display = [
        'minimum_quantity',
        'discount_amount',
        'get_categories_display'
        ]
    search_fields = ['minimum_quantity', 'discount_amount']
    list_filter = ['categories']

    def get_categories_display(self, obj):
        return ", ".join(cat.name for cat in obj.categories.all())
    get_categories_display.short_description = 'Categories'


admin.site.register(Order, OrderAdmin)
