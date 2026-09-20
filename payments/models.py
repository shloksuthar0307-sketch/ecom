from django.db import models
from orders.models import Order
from accounts.models import User

class PaymentTransaction(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment_transaction')
    provider = models.CharField(max_length=50, default='razorpay')
    provider_order_id = models.CharField(max_length=100, unique=True)
    provider_payment_id = models.CharField(max_length=100, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='INR')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.order.order_number} - {self.status}"

class SplitPayment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='split_payments')
    token = models.CharField(max_length=100, unique=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_paid = models.BooleanField(default=False)
    friend_email = models.EmailField(blank=True, null=True)
    friend_user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='split_payments_received')
    created_at = models.DateTimeField(auto_now_add=True)
