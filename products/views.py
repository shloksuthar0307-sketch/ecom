from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Product, Category, Brand

def shop_view(request):
    products = Product.objects.filter(status='published').select_related('brand').prefetch_related('images')
    
    # Filtering
    category_slug = request.GET.get('category')
    brand_slug = request.GET.get('brand')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort_by = request.GET.get('sort', 'newest')
    
    if category_slug:
        # Include subcategories using MPTT
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category__in=category.get_descendants(include_self=True))
        
    # Get brands relevant to current category/price filters
    available_brand_ids = products.values_list('brand_id', flat=True).distinct()
    brands = Brand.objects.filter(id__in=available_brand_ids)

    if brand_slug and active_category and active_category.is_leaf_node():
        products = products.filter(brand__slug=brand_slug)
    elif brand_slug:
        # Prevent orphaned brand filters if user navigates up the category tree
        brand_slug = None
        
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
        
    # Sorting
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    else:
        products = products.order_by('-created_at')
        
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Fetch the active category object to determine the active tree path
    active_category = None
    active_category_ids = []
    if category_slug:
        active_category = Category.objects.filter(slug=category_slug).first()
        if active_category:
            active_category_ids = list(active_category.get_ancestors(include_self=True).values_list('id', flat=True))

    context = {
        'products': page_obj,
        'categories': Category.objects.all(),
        'active_category': active_category,
        'active_category_ids': active_category_ids,
        'brands': brands,
        'current_category': category_slug,
        'current_brand': brand_slug,
        'min_price': min_price,
        'max_price': max_price,
        'sort_by': sort_by,
    }
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'products/partials/product_grid.html', context)
        
    return render(request, 'products/shop.html', context)

from products.services.recommendation_service import RecommendationService
from core.models import SiteConfiguration
from django.core.cache import cache
from django.db.models import Count

def product_detail(request, slug):
    product = get_object_or_404(Product.objects.prefetch_related('images', 'variants', 'reviews', 'reviews__media'), slug=slug, status='published')
    
    # Calculate review distribution
    reviews = product.reviews.filter(is_approved=True)
    total_reviews = reviews.count()
    rating_counts = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    rating_distribution = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    
    review_media_list = []
    
    if total_reviews > 0:
        for review in reviews:
            if review.rating in rating_counts:
                rating_counts[review.rating] += 1
            for media in review.media.all():
                review_media_list.append({
                    'id': media.id,
                    'url': media.file.url,
                    'type': media.media_type,
                    'review_comment': review.comment,
                    'review_rating': review.rating,
                    'user': review.user.email,
                    'created_at': review.created_at.strftime("%B %d, %Y"),
                })
        for star in rating_distribution:
            rating_distribution[star] = int((rating_counts[star] / total_reviews) * 100)
            
    avg_rating = sum(r.rating for r in reviews) / total_reviews if total_reviews > 0 else 0
    
    # AI Insight
    config = SiteConfiguration.load()
    ai_insight = None
    if config.enable_ai_insights:
        cache_key = f"ai_insight_{product.id}"
        ai_insight = cache.get(cache_key)
        if not ai_insight:
            try:
                from google import genai
                client = genai.Client()
                prompt = f"Write a 2-sentence 'Why You May Like This' summary for a product named '{product.name}' in the category '{product.category.name if product.category else 'General'}'. Short description: {product.short_description}. Based purely on these attributes."
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                )
                ai_insight = response.text.strip()
                cache.set(cache_key, ai_insight, 60*60*24)
            except Exception as e:
                pass

    # Frequently Bought Together
    from orders.models import OrderItem
    frequently_bought_ids = OrderItem.objects.filter(
        order__items__product=product
    ).exclude(
        product=product
    ).values('product_id').annotate(
        times_bought=Count('product_id')
    ).order_by('-times_bought')[:10]

    freq_product_ids = [item['product_id'] for item in frequently_bought_ids if item['product_id']]
    
    if freq_product_ids:
        recommended_qs = Product.objects.filter(id__in=freq_product_ids, status='published')
        recommended = list(recommended_qs)
        recommended.sort(key=lambda p: freq_product_ids.index(p.id))
    else:
        recommended_qs = Product.objects.filter(status='published').exclude(id=product.id)
        same_category = recommended_qs.filter(category=product.category) if product.category else Product.objects.none()
        
        recommended = list(same_category[:10])
        if len(recommended) < 10 and product.brand:
            same_brand = recommended_qs.filter(brand=product.brand).exclude(id__in=[p.id for p in recommended])
            recommended.extend(list(same_brand[:10 - len(recommended)]))
            
    import json
    context = {
        'product': product,
        'reviews': reviews,
        'review_media_list': review_media_list,
        'review_media_json': json.dumps(review_media_list),
        'total_reviews': total_reviews,
        'rating_distribution': rating_distribution,
        'rating_counts': rating_counts,
        'avg_rating': round(avg_rating, 1),
        'recommended_products': recommended,
        'ai_insight': ai_insight,
    }

    # Dynamic Pricing Engine: Increase views_count and recalculate price
    product.views_count += 1
    product.save(update_fields=['views_count'])
    
    from pricing.services import calculate_dynamic_price
    calculate_dynamic_price(product)
    
    # Reload product to get the potentially updated price
    product.refresh_from_db()
    context['product'] = product
    
    # Get price history for Chart.js
    price_history = product.price_history.all().order_by('created_at')
    
    # Calculate if price is trending upward
    trending_upward = False
    if price_history.count() >= 2:
        recent_prices = price_history.order_by('-created_at')[:2]
        if recent_prices[0].new_price > recent_prices[1].new_price:
            trending_upward = True
    
    context['price_history'] = price_history
    context['trending_upward'] = trending_upward

    return render(request, 'products/product_detail.html', context)

def quick_view(request, slug):
    product = get_object_or_404(Product.objects.prefetch_related('images', 'variants'), slug=slug, status='published')
    return render(request, 'products/quick_view.html', {'product': product})

def search_view(request):
    query = request.GET.get('q', '').strip()
    products = Product.objects.none()
    
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(short_description__icontains=query) |
            Q(description__icontains=query) |
            Q(brand__name__icontains=query) |
            Q(category__name__icontains=query) |
            Q(sku__icontains=query),
            status='published'
        ).select_related('brand').prefetch_related('images').distinct()
        
    # Sort
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    else:
        products = products.order_by('-created_at')
        
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'query': query,
        'products': page_obj,
        'result_count': products.count(),
        'sort_by': sort_by
    }
    return render(request, 'products/search_results.html', context)

def search_suggestions(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return render(request, 'products/search_suggestions.html', {'products': []})
        
    products = Product.objects.filter(
        Q(name__icontains=query) |
        Q(brand__name__icontains=query) |
        Q(category__name__icontains=query),
        status='published'
    ).select_related('brand').prefetch_related('images').distinct()[:5]
    
    return render(request, 'products/search_suggestions.html', {'products': products, 'query': query})

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.shortcuts import redirect
from .models import Review

@login_required
@require_POST
def add_review(request, product_id):
    from orders.models import OrderItem
    from .models import Review, ReviewMedia
    
    product = get_object_or_404(Product, id=product_id)
    rating = int(request.POST.get('rating', 5))
    comment = request.POST.get('comment', '')
    
    has_purchased = OrderItem.objects.filter(
        order__user=request.user, 
        product=product, 
        order__status__in=['delivered', 'shipped', 'completed']
    ).exists()

    review, created = Review.objects.update_or_create(
        product=product,
        user=request.user,
        defaults={'rating': rating, 'comment': comment, 'is_verified': has_purchased, 'is_approved': True}
    )
    
    media_files = request.FILES.getlist('media')
    for file in media_files:
        if file.content_type.startswith('image/'):
            media_type = 'image'
        elif file.content_type.startswith('video/'):
            media_type = 'video'
        else:
            continue
        ReviewMedia.objects.create(review=review, file=file, media_type=media_type)
    
    if created:
        messages.success(request, "Review added successfully!")
    else:
        messages.success(request, "Review updated successfully!")
        
    return redirect('product_detail', product.slug)

def compare_view(request):
    if request.method == 'POST':
        product_ids = request.POST.getlist('product_ids')
    else:
        product_ids = request.GET.getlist('product_ids')
        
    # If the user sends product_ids as a single comma-separated string
    if len(product_ids) == 1 and ',' in product_ids[0]:
        product_ids = product_ids[0].split(',')
        
    products = Product.objects.filter(id__in=product_ids)
    
    serialized_products = []
    for p in products:
        serialized_products.append({
            'name': p.name,
            'price': float(p.price),
            'brand': p.brand.name if p.brand else None,
            'short_description': p.short_description,
            'description': p.description,
            'category': p.category.name if p.category else None,
        })
        
    from google import genai
    from pydantic import BaseModel, Field
    import json
    
    class Comparison(BaseModel):
        table_markdown: str = Field(description="A markdown table comparing the key features of the products")
        key_differences: str = Field(description="A short summary of the key differences between the products")
        
    try:
        client = genai.Client()
        prompt = f"Compare these products factually based on the provided data: {json.dumps(serialized_products)}. Provide a markdown comparison table and a summary of key differences. Do not hallucinate specs."
        interaction = client.interactions.create(
            model='gemini-3.8-flash',
            input=prompt,
            response_format=[
                {
                    "type": "text",
                    "mime_type": "application/json",
                    "schema": Comparison.model_json_schema(),
                }
            ],
        )
        response_text = interaction.output_text.strip()
        result = json.loads(response_text)
    except Exception as e:
        result = {'table_markdown': 'Error generating comparison.', 'key_differences': str(e)}
        
    return render(request, 'products/compare.html', {
        'products': products,
        'comparison': result
    })
