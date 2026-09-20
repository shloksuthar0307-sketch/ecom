from django.conf import settings
from products.models import Product, ProductVariant
from .models import Cart as DbCart, CartItem as DbCartItem
from coupons.models import Coupon

class Cart:
    def __init__(self, request):
        self.session = request.session
        self.request = request
        cart_id = self.session.get('cart_id')
        self.coupon_id = self.session.get('coupon_id')
        
        if request.user.is_authenticated:
            self.db_cart, created = DbCart.objects.get_or_create(user=request.user)
            if cart_id and not created:
                try:
                    session_cart = DbCart.objects.get(id=cart_id, user__isnull=True)
                    self._merge_carts(session_cart, self.db_cart)
                    session_cart.delete()
                except DbCart.DoesNotExist:
                    pass
            self.session['cart_id'] = self.db_cart.id
        else:
            if cart_id:
                try:
                    self.db_cart = DbCart.objects.get(id=cart_id, user__isnull=True)
                except DbCart.DoesNotExist:
                    self.db_cart = DbCart.objects.create()
                    self.session['cart_id'] = self.db_cart.id
            else:
                self.db_cart = DbCart.objects.create()
                self.session['cart_id'] = self.db_cart.id
                self.session.modified = True

    def _merge_carts(self, from_cart, to_cart):
        for item in from_cart.items.all():
            existing_item = to_cart.items.filter(product=item.product, variant=item.variant).first()
            if existing_item:
                existing_item.quantity += item.quantity
                existing_item.save()
            else:
                item.cart = to_cart
                item.save()

    def add(self, product, quantity=1, variant_id=None):
        variant = None
        if variant_id:
            try:
                variant = ProductVariant.objects.get(id=variant_id, product=product)
            except ProductVariant.DoesNotExist:
                pass
                
        item, created = DbCartItem.objects.get_or_create(
            cart=self.db_cart, 
            product=product,
            variant=variant,
            defaults={'quantity': quantity}
        )
        if not created:
            item.quantity += int(quantity)
            item.save()

    def update(self, item_id, quantity):
        try:
            item = DbCartItem.objects.get(id=item_id, cart=self.db_cart)
            if int(quantity) > 0:
                item.quantity = int(quantity)
                item.save()
            else:
                self.remove(item_id)
        except DbCartItem.DoesNotExist:
            pass

    def remove(self, item_id):
        try:
            item = DbCartItem.objects.get(id=item_id, cart=self.db_cart)
            item.delete()
        except DbCartItem.DoesNotExist:
            pass

    def clear(self):
        self.db_cart.items.all().delete()
        if 'coupon_id' in self.session:
            del self.session['coupon_id']
            self.session.modified = True

    @property
    def coupon(self):
        if self.coupon_id:
            try:
                return Coupon.objects.get(id=self.coupon_id)
            except Coupon.DoesNotExist:
                pass
        return None

    def get_subtotal(self):
        return sum(item.get_cost() for item in self.db_cart.items.all())

    def get_discount(self):
        subtotal = self.get_subtotal()
        if self.coupon and self.coupon.is_valid() and subtotal >= self.coupon.min_order_value:
            if self.coupon.discount_type == 'percentage':
                discount = (self.coupon.discount_value / 100) * subtotal
                if self.coupon.max_discount and discount > self.coupon.max_discount:
                    return self.coupon.max_discount
                return discount
            elif self.coupon.discount_type == 'fixed':
                return min(self.coupon.discount_value, subtotal)
        return 0

    def get_total_price(self):
        return self.get_subtotal() - self.get_discount()
        
    def __iter__(self):
        for item in self.db_cart.items.select_related('product', 'variant'):
            yield item
            
    def __len__(self):
        return sum(item.quantity for item in self.db_cart.items.all())
