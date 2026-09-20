from .models import Wishlist

def wishlist_processor(request):
    count = 0
    if request.user.is_authenticated:
        try:
            count = request.user.wishlist.products.count()
        except Wishlist.DoesNotExist:
            pass
    return {'wishlist_count': count}
