from django.shortcuts import render, get_object_or_404
from .models import Category
from products.models import Product
from django.core.paginator import Paginator

def get_product_list(request, category):
    # Fetch all products under this category (and subcategories)
    # Using MPTT get_descendants(include_self=True)
    products = Product.objects.filter(
        status='published',
        visibility='visible',
        category__in=category.get_descendants(include_self=True)
    ).select_related('brand', 'category').prefetch_related('images')
    
    # Sorting
    sort = request.GET.get('sort', '-created_at')
    valid_sorts = ['-created_at', 'created_at', 'price', '-price', 'name']
    if sort in valid_sorts:
        products = products.order_by(sort)
        
    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    return page_obj

def category_list(request):
    categories = Category.objects.filter(level=0, is_active=True).order_by('display_order')
    return render(request, 'categories/category_list.html', {'categories': categories})

def category_detail(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug, level=0, is_active=True)
    products = get_product_list(request, category)
    
    context = {
        'category': category,
        'current_node': category,
        'products': products,
        'breadcrumbs': category.get_ancestors(include_self=True),
    }
    return render(request, 'categories/category_detail.html', context)

def subcategory_detail(request, category_slug, subcategory_slug):
    parent = get_object_or_404(Category, slug=category_slug, level=0, is_active=True)
    subcategory = get_object_or_404(Category, slug=subcategory_slug, parent=parent, level=1, is_active=True)
    products = get_product_list(request, subcategory)
    
    context = {
        'category': parent,
        'subcategory': subcategory,
        'current_node': subcategory,
        'products': products,
        'breadcrumbs': subcategory.get_ancestors(include_self=True),
    }
    return render(request, 'categories/category_detail.html', context)

def child_category_detail(request, category_slug, subcategory_slug, child_slug):
    parent = get_object_or_404(Category, slug=category_slug, level=0, is_active=True)
    subcategory = get_object_or_404(Category, slug=subcategory_slug, parent=parent, level=1, is_active=True)
    child = get_object_or_404(Category, slug=child_slug, parent=subcategory, level=2, is_active=True)
    products = get_product_list(request, child)
    
    context = {
        'category': parent,
        'subcategory': subcategory,
        'child_category': child,
        'current_node': child,
        'products': products,
        'breadcrumbs': child.get_ancestors(include_self=True),
    }
    return render(request, 'categories/category_detail.html', context)
