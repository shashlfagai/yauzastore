from django.contrib import admin
from .models import Order


class OrderAdmin(admin.ModelAdmin):
    readonly_fields = (
        'user',
    )
    list_display = (
        'id',
        'user',
        'email',
        'status',
        'total_price',
        'created_at'
    )
    list_filter = (
        'status',
        'created_at',
        'delivery_method',
        'payment_method'
    )


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
