from django.contrib import admin
from .models import Auction, AuctionBid

@admin.register(Auction)
class AuctionAdmin(admin.ModelAdmin):
    list_display = ('product', 'start_time', 'end_time', 'starting_price', 'is_active')
    list_filter = ('is_active',)

@admin.register(AuctionBid)
class AuctionBidAdmin(admin.ModelAdmin):
    list_display = ('user', 'auction', 'amount', 'timestamp')
