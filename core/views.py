import json
from django.shortcuts import render
from django.core.cache import cache
from products.models import Product, Category
from orders.models import Order
from cart.models import Cart
from ai_assistant.services import generate_homepage_recommendations

def index(request):
    featured_products = Product.objects.filter(status='published', is_featured=True)[:8]
    categories = Category.objects.filter(parent=None)[:6]
    
    context = {
        'featured_products': featured_products,
        'categories': categories,
    }

    if request.user.is_authenticated:
        cache_key = f"homepage_recs_{request.user.id}"
        recs = cache.get(cache_key)
        
        if not recs:
            # Build context
            recent_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
            purchased_items = []
            for order in recent_orders:
                for item in order.items.all():
                    purchased_items.append(item.product_name)
                    
            cart = Cart.objects.filter(user=request.user).first()
            cart_items = []
            if cart:
                for item in cart.items.all():
                    cart_items.append(item.product.name)
            
            user_context = f"Recent purchases: {', '.join(purchased_items) if purchased_items else 'None'}. Cart items: {', '.join(cart_items) if cart_items else 'None'}."
            
            try:
                recs_json = generate_homepage_recommendations(user_context)
                if recs_json:
                    recs_data = json.loads(recs_json)
                    product_ids = recs_data.get('product_ids', [])
                    explanation = recs_data.get('explanation', '')
                    
                    if product_ids:
                        recommended_products = list(Product.objects.filter(id__in=product_ids, status='published'))
                        # To preserve order from the AI output:
                        recommended_products.sort(key=lambda p: product_ids.index(p.id) if p.id in product_ids else 999)
                        
                        recs = {
                            'explanation': explanation,
                            'products': recommended_products
                        }
                        cache.set(cache_key, recs, 86400)
            except Exception as e:
                print(f"Gemini error: {e}")
                pass
                
        if recs:
            context['ai_recommendations'] = recs

    return render(request, 'core/index.html', context)

def about(request):
    return render(request, 'core/about.html')
