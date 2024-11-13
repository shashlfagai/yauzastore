from .models import Order


def cart_item_count(request):
    if request.user.is_authenticated:
        order = Order.objects.filter(
            user=request.user, status='pending'
            ).first()
        return {'cart_item_count': order.items.count() if order else 0}
    else:
        cart = request.session.get('cart', {})
        return {
            'cart_item_count': sum(item['quantity'] for item in cart.values())
            }
