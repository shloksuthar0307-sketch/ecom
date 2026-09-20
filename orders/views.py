from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from cart.cart import Cart
from accounts.models import Address
from .models import Order, OrderItem, GroupPurchase
from products.models import Product
import uuid

@login_required
def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.warning(request, "Your cart is empty.")
        return redirect('cart_detail')
        
    addresses = request.user.addresses.all()
    
    if request.method == 'POST':
        address_id = request.POST.get('address_id')
        
        if address_id:
            try:
                address = Address.objects.get(id=address_id, user=request.user)
                
                # Create Order
                order = Order.objects.create(
                    user=request.user,
                    order_number=str(uuid.uuid4()).split('-')[0].upper(),
                    shipping_address=address,
                    billing_address=address,
                    coupon=cart.coupon,
                    subtotal=cart.get_subtotal(),
                    discount=cart.get_discount(),
                    total=cart.get_total_price() # Add shipping/tax logic later
                )
                
                # Increment coupon usage
                if cart.coupon:
                    cart.coupon.used_count += 1
                    cart.coupon.save()
                
                # Create Order Items (snapshotting prices)
                for item in cart:
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        variant=item.variant,
                        product_name=item.product.name,
                        variant_name=item.variant.name if item.variant else None,
                        price=item.get_cost() / item.quantity,
                        quantity=item.quantity
                    )
                
                # Clear cart
                cart.clear()
                
                # Emit purchase event to product groups
                from channels.layers import get_channel_layer
                from asgiref.sync import async_to_sync
                
                channel_layer = get_channel_layer()
                for item in order.items.all():
                    async_to_sync(channel_layer.group_send)(
                        f'product_{item.product.id}',
                        {
                            'type': 'purchase_update'
                        }
                    )
                
                # Create Razorpay Order
                from payments.services import PaymentService
                rzp_id = PaymentService.create_razorpay_order(order)
                if rzp_id:
                    return redirect('payment_checkout', order.order_number)
                
                messages.success(request, f"Order {order.order_number} created successfully!")
                return redirect('order_success', order.order_number)
                
            except Address.DoesNotExist:
                messages.error(request, "Invalid address selected.")
        else:
            messages.error(request, "Please select a shipping address.")
            
    return render(request, 'orders/checkout.html', {
        'cart': cart,
        'addresses': addresses
    })

@login_required
def order_success(request, order_number):
    order = Order.objects.get(order_number=order_number)
    
    from payments.models import SplitPayment
    split_payment = SplitPayment.objects.filter(order=order, is_paid=False, friend_user__isnull=True).first()
    
    # Get unique gift configs for this order
    gift_configs = set()
    for item in order.items.all():
        if item.gift_configuration:
            gift_configs.add(item.gift_configuration)
    
    return render(request, 'orders/success.html', {
        'order_number': order_number,
        'split_payment': split_payment,
        'gift_configs': gift_configs
    })

@login_required
def create_group_buy(request, product_id):
    product = Product.objects.get(id=product_id)
    token = str(uuid.uuid4())
    group = GroupPurchase.objects.create(
        product=product,
        token=token,
        creator=request.user,
        req_members=3,
        discount=15.00
    )
    group.members.add(request.user)
    return redirect('group_buy_detail', token=group.token)

@login_required
def group_buy_detail(request, token):
    group = GroupPurchase.objects.get(token=token)
    
    if request.method == 'POST':
        if not group.is_locked and request.user not in group.members.all():
            group.members.add(request.user)
            if group.is_full():
                group.is_locked = True
                group.save()
            
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'groupbuy_{group.token}',
                {
                    'type': 'groupbuy_update',
                    'count': group.members.count(),
                    'is_locked': group.is_locked
                }
            )
        return redirect('group_buy_detail', token=token)
        
    return render(request, 'orders/group_buy_detail.html', {'group': group})

@login_required
def reveal_mystery_box(request, token):
    from .models import MysteryBox
    box = get_object_or_404(MysteryBox, token=token, order_item__order__user=request.user)
    
    if request.method == 'POST':
        # Mark as revealed via ajax or form submit
        box.is_revealed = True
        box.save()
        return JsonResponse({'status': 'success'})
        
    return render(request, 'orders/mystery_box_reveal.html', {'box': box})
