from django.urls import path
from . import views

urlpatterns = [
    path(
        '',
        views.order_view,
        name='order_view'
    ),
    path(
        'remove/<int:item_id>/',
        views.remove_from_order,
        name='remove_from_order'
    ),
    path(
        'update-order-quantity/',
        views.update_order_quantity,
        name='update_order_quantity'
    ),
    path(
        'order_history/',
        views.order_history,
        name='order_history'
    ),
    path(
        'orders/<int:order_id>/',
        views.order_detail,
        name='order_detail'
    ),
    path(
        'apply_promocode',
        views.apply_promo_code,
        name='apply_promo_code'
    ),
    path(
        'making_order/',
        views.making_order_view,
        name='making_order'
    ),
    path(
        'submit_order/',
        views.submit_order,
        name='submit_order'
    )
]
