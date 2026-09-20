from django.db import models
from django.conf import settings
from django.utils import timezone
from products.models import Product

class Auction(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='auctions')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    starting_price = models.DecimalField(max_digits=10, decimal_places=2)
    min_increment = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)
    winner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='won_auctions')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def highest_bid(self):
        bid = self.bids.order_by('-amount').first()
        return bid.amount if bid else self.starting_price

    @property
    def highest_bidder(self):
        bid = self.bids.order_by('-amount').first()
        return bid.user if bid else None

    @property
    def is_live(self):
        now = timezone.now()
        return self.is_active and self.start_time <= now <= self.end_time

    def __str__(self):
        return f"Auction for {self.product.name} (ID: {self.id})"

class AuctionBid(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='auction_bids')
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name='bids')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-amount', 'timestamp']

    def __str__(self):
        return f"{self.user.email} bid {self.amount} on {self.auction.product.name}"
