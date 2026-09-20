import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from coupons.models import Coupon
from django.utils import timezone
from products.models import Product
from cart.cart import Cart

@require_POST
def apply_coupon_ajax(request):
    try:
        data = json.loads(request.body)
        code = data.get('code')
        try:
            coupon = Coupon.objects.get(
                code__iexact=code,
                valid_from__lte=timezone.now(),
                valid_to__gte=timezone.now(),
                active=True
            )
            request.session['coupon_id'] = coupon.id
            cart = Cart(request)
            return JsonResponse({
                'success': True, 
                'discount': coupon.discount, 
                'type': coupon.discount_type,
                'cart_subtotal': str(cart.get_subtotal()),
                'cart_discount': str(cart.get_discount()),
                'cart_total': str(cart.get_total_price())
            })
        except Coupon.DoesNotExist:
            request.session['coupon_id'] = None
            return JsonResponse({'success': False, 'error': 'Invalid or expired coupon'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@require_GET
def get_cart_recommendations(request):
    cart = Cart(request)
    cart_product_ids = [item.product_id for item in cart]
    
    # Simple recommendation logic: get active products not in cart, sorted randomly or by newest
    # For a real app, you might find categories of items in the cart and match those.
    recos = Product.objects.filter(is_active=True).exclude(id__in=cart_product_ids).order_by('?')[:5]
    
    products_data = []
    for p in recos:
        products_data.append({
            'name': p.name,
            'slug': p.slug,
            'price': str(p.price),
            'image': p.images.first().image.url if p.images.exists() else ''
        })
        
    return JsonResponse({'products': products_data})
