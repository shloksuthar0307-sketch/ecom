import json
from django.shortcuts import render, redirect, get_object_or_404
from core.decorators import admin_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Product, ProductImage, ProductVariant, Brand
from categories.models import Category
from django.db.models import Q
from django.core.paginator import Paginator

@admin_required
def product_list(request):
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    category_id = request.GET.get('category', '')
    
    products = Product.objects.all().select_related('category', 'brand').order_by('-created_at')
    
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(sku__icontains=query) |
            Q(brand__name__icontains=query)
        )
    if status_filter:
        products = products.filter(status=status_filter)
    if category_id:
        try:
            cat = Category.objects.get(id=category_id)
            products = products.filter(category__in=cat.get_descendants(include_self=True))
        except Category.DoesNotExist:
            pass
            
    paginator = Paginator(products, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    root_categories = Category.objects.filter(level=0)
    
    context = {
        'products': page_obj,
        'query': query,
        'status_filter': status_filter,
        'category_id': category_id,
        'root_categories': root_categories,
    }
    return render(request, 'dashboard/products/list.html', context)

@admin_required
def product_add(request):
    if request.method == 'POST':
        # Retrieve form data
        name = request.POST.get('name')
        sku = request.POST.get('sku')
        price = request.POST.get('price')
        
        # Categories mapping
        # The form passes 'child_category' which is the leaf node.
        # If no child, fallback to sub, then root.
        cat_id = request.POST.get('child_category') or request.POST.get('subcategory') or request.POST.get('category')
        
        try:
            category = Category.objects.get(id=cat_id)
            
            product = Product.objects.create(
                name=name,
                slug=request.POST.get('slug'),
                sku=sku,
                short_description=request.POST.get('short_description'),
                description=request.POST.get('description'),
                category=category,
                price=price,
                stock_quantity=request.POST.get('stock_quantity', 0),
                status=request.POST.get('status', 'draft'),
                visibility=request.POST.get('visibility', 'visible')
            )
            
            # Handle brand if present
            brand_id = request.POST.get('brand')
            if brand_id:
                product.brand_id = brand_id
                product.save()
            
            # Handle images (Drag & Drop placeholder logic)
            # Typically you'd iterate over request.FILES.getlist('images')
            for f in request.FILES.getlist('images'):
                ProductImage.objects.create(product=product, image=f)
                
            # Handle variants (JSON payload from frontend)
            variants_data = request.POST.get('variants_data')
            if variants_data:
                variants = json.loads(variants_data)
                for v in variants:
                    ProductVariant.objects.create(
                        product=product,
                        name=v['name'],
                        sku=v['sku'],
                        price=v['price'],
                        stock=v['stock']
                    )

            messages.success(request, f"Product {name} created.")
            return redirect('dashboard_products')
            
        except Exception as e:
            messages.error(request, f"Error creating product: {str(e)}")
            
    categories = Category.objects.filter(level=0)
    brands = Brand.objects.all()
    return render(request, 'dashboard/products/form.html', {
        'categories': categories,
        'brands': brands,
    })

# AJAX Endpoint for Dynamic Selectors
@admin_required
def get_child_categories(request, parent_id):
    try:
        parent = Category.objects.get(id=parent_id)
        children = parent.get_children().values('id', 'name')
        return JsonResponse({'children': list(children)})
    except Category.DoesNotExist:
        return JsonResponse({'children': []})
