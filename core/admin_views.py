from django.shortcuts import render
from core.decorators import admin_required
from orders.models import Order
from products.models import Product
from accounts.models import User
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

@admin_required
def custom_dashboard(request):
    # Basic metrics
    total_revenue = Order.objects.exclude(status__in=['cancelled', 'refunded']).aggregate(Sum('total'))['total__sum'] or 0
    total_orders = Order.objects.count()
    total_customers = User.objects.count()
    
    # Recent orders
    recent_orders = Order.objects.all().order_by('-created_at')[:5]
    
    # Top products (simple implementation)
    top_products = Product.objects.annotate(
        order_count=Count('orderitem')
    ).order_by('-order_count')[:5]

    context = {
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'total_customers': total_customers,
        'recent_orders': recent_orders,
        'top_products': top_products,
    }
    return render(request, 'core/dashboard.html', context)

from django.http import JsonResponse
from django.db.models.functions import TruncDate
from django.db.models import F
from orders.models import OrderItem

@admin_required
def analytics_data(request):
    today = timezone.now().date()
    start_date = today - timedelta(days=29)
    
    # Last 30 Days Revenue
    orders = Order.objects.filter(
        created_at__date__gte=start_date
    ).exclude(status__in=['cancelled', 'refunded'])
    
    daily_revenue = orders.annotate(date=TruncDate('created_at')).values('date').annotate(
        total=Sum('total')
    ).order_by('date')
    
    revenue_dict = {item['date']: item['total'] for item in daily_revenue if item['date']}
    
    trend_labels = []
    trend_data = []
    for i in range(30):
        d = start_date + timedelta(days=i)
        trend_labels.append(d.strftime('%b %d'))
        trend_data.append(float(revenue_dict.get(d, 0)))
        
    # Top Selling Categories (by Revenue)
    top_categories = OrderItem.objects.filter(
        order__created_at__date__gte=start_date
    ).exclude(order__status__in=['cancelled', 'refunded']).values(
        'product__category__name'
    ).annotate(
        revenue=Sum(F('price') * F('quantity'))
    ).order_by('-revenue')[:5]
    
    cat_labels = []
    cat_data = []
    for cat in top_categories:
        name = cat['product__category__name'] or 'Unknown'
        cat_labels.append(name)
        cat_data.append(float(cat['revenue'] or 0))
        
    return JsonResponse({
        'revenue_trend': {
            'labels': trend_labels,
            'data': trend_data
        },
        'top_categories': {
            'labels': cat_labels,
            'data': cat_data
        }
    })
