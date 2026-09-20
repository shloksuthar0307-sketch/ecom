from .models import Category

def category_menu(request):
    # Fetch root categories with their children (Level 1) and grandchildren (Level 2)
    # prefetch_related is very efficient here to avoid N+1 queries in the mega menu
    root_categories = Category.objects.filter(level=0, is_active=True).prefetch_related('children__children').order_by('display_order')
    return {'mega_menu_categories': root_categories}
