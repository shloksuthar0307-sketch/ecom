from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages
from products.models import Product
from .cart import Cart

def cart_detail(request):
    cart = Cart(request)
    return render(request, 'cart/cart_detail.html', {'cart': cart})

@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    variant_id = request.POST.get('variant_id')
    
    cart.add(product=product, quantity=quantity, variant_id=variant_id)
    messages.success(request, f"Added {product.name} to your cart.")
    
    # Simple redirect back to where we came from, or cart detail
    return redirect(request.META.get('HTTP_REFERER', 'cart_detail'))

@require_POST
def cart_update(request, item_id):
    cart = Cart(request)
    quantity = int(request.POST.get('quantity', 1))
    cart.update(item_id=item_id, quantity=quantity)
    return redirect('cart_detail')

@require_POST
def cart_remove(request, item_id):
    cart = Cart(request)
    cart.remove(item_id)
    messages.info(request, "Item removed from cart.")
    return redirect('cart_detail')

@require_POST
def apply_coupon(request):
    code = request.POST.get('coupon_code')
    try:
        from coupons.models import Coupon
        coupon = Coupon.objects.get(code__iexact=code)
        if coupon.is_valid():
            request.session['coupon_id'] = coupon.id
            messages.success(request, f"Coupon '{code}' applied successfully!")
        else:
            messages.error(request, "Coupon is expired or invalid.")
    except Coupon.DoesNotExist:
        messages.error(request, "Coupon not found.")
    return redirect('cart_detail')
