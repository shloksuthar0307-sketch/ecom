import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from core.decorators import admin_required
from .models import Lookbook, LookbookItem
from products.models import Product

def lookbook_index(request):
    lookbooks = Lookbook.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'lookbook/index.html', {'lookbooks': lookbooks})

def lookbook_detail(request, slug):
    lookbook = get_object_or_404(Lookbook, slug=slug, is_active=True)
    return render(request, 'lookbook/detail.html', {'lookbook': lookbook})

@admin_required
def lookbook_builder(request, pk):
    lookbook = get_object_or_404(Lookbook, pk=pk)
    return render(request, 'lookbook/builder.html', {'lookbook': lookbook})

@admin_required
def lookbook_product_search(request):
    query = request.GET.get('q', '')
    products = Product.objects.filter(name__icontains=query, status='published')[:10]
    data = [{'id': p.id, 'name': p.name, 'price': str(p.price)} for p in products]
    return JsonResponse({'products': data})

@admin_required
@require_POST
def lookbook_save_item(request, pk):
    lookbook = get_object_or_404(Lookbook, pk=pk)
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        
        if item_id:
            item = get_object_or_404(LookbookItem, id=item_id, lookbook=lookbook)
            if data.get('delete'):
                item.delete()
                return JsonResponse({'status': 'deleted'})
                
        product_id = data.get('product_id')
        x_position = data.get('x_position')
        y_position = data.get('y_position')
        
        if not product_id or x_position is None or y_position is None:
            return JsonResponse({'error': 'Missing data'}, status=400)
            
        product = get_object_or_404(Product, id=product_id)
        
        if item_id:
            item.product = product
            item.x_position = float(x_position)
            item.y_position = float(y_position)
            item.save()
        else:
            item = LookbookItem.objects.create(
                lookbook=lookbook,
                product=product,
                x_position=float(x_position),
                y_position=float(y_position)
            )
            
        return JsonResponse({
            'status': 'success',
            'item': {
                'id': item.id,
                'product_id': item.product.id,
                'product_name': item.product.name,
                'x_position': item.x_position,
                'y_position': item.y_position
            }
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
