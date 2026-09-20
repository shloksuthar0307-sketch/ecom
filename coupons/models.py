from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

class Coupon(models.Model):
    DISCOUNT_TYPES = (
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    )
    
    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES, default='percentage')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, help_text="Percentage (0-100) or Fixed Amount")
    
    min_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    start_date = models.DateTimeField(default=timezone.now)
    expiry_date = models.DateTimeField()
    
    usage_limit = models.PositiveIntegerField(null=True, blank=True, help_text="Total number of times this coupon can be used")
    used_count = models.PositiveIntegerField(default=0)
    
    active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.code
        
    def is_valid(self):
        now = timezone.now()
        if not self.active:
            return False
        if self.start_date > now or self.expiry_date < now:
            return False
        if self.usage_limit and self.used_count >= self.usage_limit:
            return False
        return True
