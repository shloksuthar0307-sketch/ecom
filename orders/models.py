from django.db import models
from accounts.models import User, Address
from products.models import Product, ProductVariant
from coupons.models import Coupon

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    )
    
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    order_number = models.CharField(max_length=50, unique=True)
    
    shipping_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, related_name='shipping_orders')
    billing_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, related_name='billing_orders')
    
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Order {self.order_number}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Snapshots
    product_name = models.CharField(max_length=255)
    variant_name = models.CharField(max_length=100, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    gift_configuration = models.ForeignKey('gifts.GiftConfiguration', on_delete=models.SET_NULL, null=True, blank=True, related_name='order_items')
    
    def __str__(self):
        return f"{self.quantity}x {self.product_name}"
        
    def get_cost(self):
        return self.price * self.quantity

class GroupPurchase(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='group_purchases')
    token = models.CharField(max_length=100, unique=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')
    req_members = models.PositiveIntegerField(default=3)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)
    members = models.ManyToManyField(User, related_name='joined_groups', blank=True)
    is_locked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_full(self):
        return self.members.count() >= self.req_members

class MysteryBox(models.Model):
    order_item = models.OneToOneField(OrderItem, related_name='mystery_box', on_delete=models.CASCADE)
    token = models.CharField(max_length=100, unique=True)
    products = models.ManyToManyField(Product, related_name='mystery_boxes')
    is_revealed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Mystery Box for {self.order_item}"
