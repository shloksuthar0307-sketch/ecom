import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from cart.cart import Cart
from accounts.models import Address
from orders.models import Order, OrderItem
from payments.services import PaymentService
from django.conf import settings
import uuid

@login_required
@require_POST
def process_checkout_ajax(request):
    try:
        data = json.loads(request.body)
        address_id = data.get('address_id')
        
        if not address_id:
            return JsonResponse({'success': False, 'error': 'No address selected'}, status=400)
            
        cart = Cart(request)
        if len(cart) == 0:
            return JsonResponse({'success': False, 'error': 'Cart is empty'}, status=400)
            
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
            total=cart.get_total_price()
        )
        
        if cart.coupon:
            cart.coupon.used_count += 1
            cart.coupon.save()
            
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
            
        is_split = data.get('is_split', False)
        
        if is_split:
            split_amount = order.total / 2
            original_total = order.total
            order.total = split_amount
            rzp_id = PaymentService.create_razorpay_order(order)
            order.total = original_total
            
            from payments.models import SplitPayment
            SplitPayment.objects.create(
                order=order,
                token=str(uuid.uuid4()),
                amount_paid=split_amount,
                is_paid=False
            )
            amount_to_pay = split_amount
        else:
            rzp_id = PaymentService.create_razorpay_order(order)
            amount_to_pay = order.total
        
        return JsonResponse({
            'success': True, 
            'order_number': order.order_number,
            'razorpay_order_id': rzp_id,
            'amount': int(amount_to_pay * 100),
            'currency': 'INR',
            'key': settings.RAZORPAY_KEY_ID,
            'user_name': f"{request.user.first_name} {request.user.last_name}",
            'user_email': request.user.email,
            'user_phone': address.phone
        })
        
    except Address.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Invalid address'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
