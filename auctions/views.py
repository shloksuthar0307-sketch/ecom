from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Auction, AuctionBid
from orders.models import Order, OrderItem
import uuid

def auction_list(request):
    now = timezone.now()
    live_auctions = Auction.objects.filter(is_active=True, start_time__lte=now, end_time__gte=now)
    upcoming_auctions = Auction.objects.filter(is_active=True, start_time__gt=now)
    past_auctions = Auction.objects.filter(is_active=True, end_time__lt=now)

    return render(request, 'auctions/list.html', {
        'live_auctions': live_auctions,
        'upcoming_auctions': upcoming_auctions,
        'past_auctions': past_auctions,
    })

def auction_detail(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id)
    bids = auction.bids.all()
    
    return render(request, 'auctions/detail.html', {
        'auction': auction,
        'bids': bids,
    })

@login_required
def auction_checkout(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id)
    now = timezone.now()
    
    # Must be past end time
    if auction.end_time > now:
        messages.error(request, "Auction has not ended yet.")
        return redirect('auction_detail', auction_id=auction.id)
    
    # Find highest bid
    highest_bid = auction.bids.order_by('-amount').first()
    if not highest_bid:
        messages.info(request, "No bids were placed on this auction.")
        return redirect('auction_detail', auction_id=auction.id)
        
    if highest_bid.user != request.user:
        messages.error(request, "You are not the winner of this auction.")
        return redirect('auction_detail', auction_id=auction.id)
        
    # Check if order already exists for this auction (via session or simple check, but since we don't have auction field in Order, we generate a specific order_number format)
    order_number = f"AUC-{auction.id}-{request.user.id}"
    order = Order.objects.filter(order_number=order_number).first()
    
    if not order:
        # Create order
        order = Order.objects.create(
            user=request.user,
            order_number=order_number,
            subtotal=highest_bid.amount,
            total=highest_bid.amount,
            status='pending',
            payment_status='pending'
        )
        # Create order item
        OrderItem.objects.create(
            order=order,
            product=auction.product,
            product_name=auction.product.name,
            price=highest_bid.amount,
            quantity=1
        )
        
    return redirect('payment_checkout', order_number=order.order_number)
