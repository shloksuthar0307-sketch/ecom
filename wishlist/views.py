from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from products.models import Product
from .models import Wishlist

@login_required
def wishlist_detail(request):
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    return render(request, 'wishlist/wishlist_detail.html', {'wishlist': wishlist})

@login_required
@require_POST
def wishlist_toggle(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    
    if product in wishlist.products.all():
        wishlist.products.remove(product)
        messages.info(request, f"Removed {product.name} from your wishlist.")
    else:
        wishlist.products.add(product)
        messages.success(request, f"Added {product.name} to your wishlist.")
        
    return redirect(request.META.get('HTTP_REFERER', 'wishlist_detail'))
