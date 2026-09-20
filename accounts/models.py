from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    email = models.EmailField(_('email address'), unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    profile_photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    
    # Use email as the primary identifier instead of username for e-commerce
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    title = models.CharField(max_length=50, help_text="e.g. Home, Work")
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=20)
    street_address = models.CharField(max_length=250)
    apartment_address = models.CharField(max_length=250, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    is_default_shipping = models.BooleanField(default=False)
    is_default_billing = models.BooleanField(default=False)
    
    class Meta:
        verbose_name_plural = "Addresses"

    def __str__(self):
        return f"{self.title} - {self.user.email}"

class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    loyalty_points = models.IntegerField(default=0)
    lifetime_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.user.email} Profile"
        
    @property
    def current_tier(self):
        if self.lifetime_spent >= 100000:
            return "VIP"
        elif self.lifetime_spent >= 50000:
            return "Gold"
        elif self.lifetime_spent >= 10000:
            return "Silver"
        return "Bronze"
        
    @property
    def next_tier(self):
        if self.lifetime_spent < 10000:
            return {"name": "Silver", "threshold": 10000}
        elif self.lifetime_spent < 50000:
            return {"name": "Gold", "threshold": 50000}
        elif self.lifetime_spent < 100000:
            return {"name": "VIP", "threshold": 100000}
        return None

    @property
    def spend_to_next_tier(self):
        next_tier_info = self.next_tier
        if next_tier_info:
            return float(next_tier_info["threshold"]) - float(self.lifetime_spent)
        return 0
        
    @property
    def progress_percentage(self):
        if self.lifetime_spent >= 100000:
            return 100
        elif self.lifetime_spent >= 50000:
            current_base = 50000
            next_base = 100000
        elif self.lifetime_spent >= 10000:
            current_base = 10000
            next_base = 50000
        else:
            current_base = 0
            next_base = 10000
            
        progress = float(self.lifetime_spent) - current_base
        total_required = next_base - current_base
        return min(int((progress / total_required) * 100), 100)

class LoyaltyTransaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loyalty_transactions')
    amount = models.IntegerField()
    transaction_type = models.CharField(max_length=50) # e.g. 'earned', 'spent'
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.amount} ({self.transaction_type})"
