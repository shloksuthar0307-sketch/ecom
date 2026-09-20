import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from products.models import Product
from cart.models import CartItem
from cart.cart import Cart
from .models import GiftConfiguration

def gift_studio(request):
    products = Product.objects.filter(is_active=True)
    # Get Cloudinary info from settings if needed
    from django.conf import settings
    cloud_name = settings.CLOUDINARY_STORAGE.get('CLOUD_NAME', '')
    return render(request, 'gifts/studio.html', {
        'products': products,
        'cloud_name': cloud_name,
    })

@csrf_exempt
def save_gift_config(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            box_design = data.get('box_design')
            video_url = data.get('video_url')
            message = data.get('message')
            product_ids = data.get('product_ids', [])
            
            if not (3 <= len(product_ids) <= 5):
                return JsonResponse({'error': 'Please select between 3 and 5 products.'}, status=400)
                
            # Create the Gift Config
            config = GiftConfiguration.objects.create(
                box_design=box_design,
                video_url=video_url,
                message=message
            )
            
            # Add to cart
            cart_obj = Cart(request)
            db_cart = cart_obj.db_cart
            
            for pid in product_ids:
                product = Product.objects.get(id=pid)
                # Ensure unique cart item for gift configuration
                CartItem.objects.create(
                    cart=db_cart,
                    product=product,
                    quantity=1,
                    gift_configuration=config
                )
                
            return JsonResponse({'success': True, 'redirect_url': '/cart/'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method.'}, status=405)

def recipient_page(request, qr_token):
    config = get_object_or_404(GiftConfiguration, qr_token=qr_token)
    return render(request, 'gifts/recipient.html', {'config': config})

import time
import cloudinary.utils
from django.conf import settings

def generate_signature(request):
    timestamp = int(time.time())
    api_secret = settings.CLOUDINARY_STORAGE.get('API_SECRET')
    signature = cloudinary.utils.api_sign_request({'timestamp': timestamp}, api_secret)
    return JsonResponse({
        'signature': signature,
        'timestamp': timestamp,
        'api_key': settings.CLOUDINARY_STORAGE.get('API_KEY'),
        'cloud_name': settings.CLOUDINARY_STORAGE.get('CLOUD_NAME')
    })
