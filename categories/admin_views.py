import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count
from core.decorators import admin_required
from .models import Category

@admin_required
def category_list(request):
    categories = Category.objects.filter(level=0).annotate(product_count=Count('products')).prefetch_related('children__children')
    subcategories = Category.objects.filter(level=1).annotate(product_count=Count('products')).prefetch_related('children')
    child_categories = Category.objects.filter(level=2).annotate(product_count=Count('products'))
    
    metrics = {
        'total': Category.objects.count(),
        'categories': categories.count(),
        'subcategories': subcategories.count(),
        'child_categories': child_categories.count(),
    }
    
    return render(request, 'dashboard/categories/list.html', {
        'categories': categories,
        'subcategories': subcategories,
        'child_categories': child_categories,
        'metrics': metrics
    })

@admin_required
def category_add(request, level=0):
    if request.method == 'POST':
        name = request.POST.get('name')
        slug = request.POST.get('slug')
        parent_id = request.POST.get('parent')
        
        try:
            parent = Category.objects.get(id=parent_id) if parent_id else None
            Category.objects.create(
                name=name,
                slug=slug,
                parent=parent,
                description=request.POST.get('description'),
                image=request.FILES.get('image'),
                is_active=request.POST.get('is_active') == 'on',
                is_featured=request.POST.get('is_featured') == 'on',
                display_order=request.POST.get('display_order', 0)
            )
            messages.success(request, f"{name} created successfully.")
            return redirect('dashboard_category_list')
        except Exception as e:
            messages.error(request, str(e))
            
    # For level 1 (Subcategory), parents are level 0. For level 2 (Child), parents are level 1
    # However, for level 2, in the form we want to select Root Category first, then Subcategory via AJAX.
    root_categories = Category.objects.filter(level=0)
    return render(request, 'dashboard/categories/form.html', {
        'level': level,
        'root_categories': root_categories,
        'is_edit': False
    })

@admin_required
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    level = category.level
    
    if request.method == 'POST':
        category.name = request.POST.get('name')
        category.slug = request.POST.get('slug')
        
        if level > 0:
            parent_id = request.POST.get('parent')
            if parent_id:
                category.parent = Category.objects.get(id=parent_id)
                
        category.description = request.POST.get('description')
        if 'image' in request.FILES:
            category.image = request.FILES.get('image')
            
        category.is_active = request.POST.get('is_active') == 'on'
        category.is_featured = request.POST.get('is_featured') == 'on'
        category.display_order = request.POST.get('display_order', 0)
        
        try:
            category.save()
            messages.success(request, f"{category.name} updated successfully.")
            return redirect('dashboard_category_list')
        except Exception as e:
            messages.error(request, str(e))
            
    root_categories = Category.objects.filter(level=0)
    current_root = None
    if level == 2 and category.parent:
        current_root = category.parent.parent

    return render(request, 'dashboard/categories/form.html', {
        'category': category,
        'level': level,
        'root_categories': root_categories,
        'current_root': current_root,
        'is_edit': True
    })

@admin_required
def category_delete(request, pk):
    cat = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        if cat.get_descendant_count() > 0 or cat.products.exists():
            messages.error(request, "Cannot delete category containing products or subcategories.")
        else:
            cat.delete()
            messages.success(request, "Category deleted.")
        return redirect('dashboard_category_list')
    return render(request, 'dashboard/categories/delete_confirm.html', {'category': cat})

@admin_required
def ajax_load_subcategories(request):
    category_id = request.GET.get('category_id')
    subcategories = Category.objects.filter(parent_id=category_id).order_by('name')
    return JsonResponse(list(subcategories.values('id', 'name')), safe=False)
