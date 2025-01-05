from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Product,
    ProductSize,
    Promo,
    ProductImage,
    StockBanner,
    PartnerProjects
)
from orders.models import PromoCode, BulkDiscount


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image_tag', 'image')
    readonly_fields = ('image_tag',)

    def image_tag(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 100px; height: 100px;" />',
                obj.image.url
            )
        return "Нет изображения"

    image_tag.short_description = 'Предпросмотр'


class ProductSizeInline(admin.TabularInline):
    model = ProductSize
    extra = 1


class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline, ProductSizeInline]
    list_display = ['name', 'price', 'designer', 'created_at', 'first_image']
    search_fields = ['name', 'description', 'designer']
    list_filter = ['created_at', 'categories']
    filter_horizontal = ['categories', 'subcategories']

    def first_image(self, obj):
        if obj.get_first_image():
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px;" />',
                obj.get_first_image()
            )
        return "Нет изображения"
    first_image.short_description = 'Изображение'


class PromoCodeInline(admin.TabularInline):
    model = PromoCode
    extra = 1


class BulkDiscountInline(admin.TabularInline):
    model = BulkDiscount
    extra = 1


class PromoAdmin(admin.ModelAdmin):
    inlines = [PromoCodeInline, BulkDiscountInline]
    list_display = ['name']
    search_fields = ['name']
    filter_horizontal = ['categories']


class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent_category')
    list_filter = ('parent_category',)
    search_fields = ('name',)


class PartnerProjectsAdmin(admin.ModelAdmin):
    list_display = (
        'form_type',
        'project_name',
        'phone',
        'first_name',
        'status',
        'created_at',
        'agree_to_privacy_policy'
    )
    list_filter = ('form_type', 'status', 'created_at')
    search_fields = ('first_name', 'last_name', 'phone', 'project_name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at','agree_to_privacy_policy',)


admin.site.register(Product, ProductAdmin)
admin.site.register(StockBanner)
admin.site.register(Promo, PromoAdmin)
admin.site.register(PartnerProjects, PartnerProjectsAdmin)
