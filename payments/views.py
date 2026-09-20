import json
import uuid
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from .services import PaymentService
from .models import PaymentTransaction
from django.db import transaction
from core.services.email_service import EmailService
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from orders.models import Order, OrderItem
from orders.utils import curate_mystery_box
from accounts.models import Address, CustomerProfile
from cart.cart import Cart
from django.contrib import messages

@csrf_exempt
@require_POST
def razorpay_webhook(request):
    webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET
    webhook_signature = request.headers.get('X-Razorpay-Signature')
    if not webhook_signature:
        return HttpResponseBadRequest("Missing signature")
    try:
        client = PaymentService.get_client()
        client.utility.verify_webhook_signature(
            request.body.decode('utf-8'),
            webhook_signature,
            webhook_secret
        )
    except Exception as e:
        return HttpResponseBadRequest("Invalid signature")
    try:
        payload = json.loads(request.body)
        event = payload.get('event')
        if event == 'order.paid':
            payment_entity = payload['payload']['payment']['entity']
            order_id = payment_entity['order_id']
            payment_id = payment_entity['id']
            with transaction.atomic():
                try:
                    pt = PaymentTransaction.objects.select_for_update().get(provider_order_id=order_id)
                    if pt.status != 'paid':
                        pt.status = 'paid'
                        pt.provider_payment_id = payment_id
                        pt.save()
                        order = pt.order
                        order.status = 'processing'
                        order.save()
                        try:
                            EmailService.send_order_confirmation_email(order)
                        except Exception:
                            pass
                except PaymentTransaction.DoesNotExist:
                    pass
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")
    return HttpResponse("OK")

@login_required
def payment_checkout(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    try:
        pt = order.payment_transaction
    except PaymentTransaction.DoesNotExist:
        messages.error(request, "Payment transaction not found.")
        return redirect('account_orders')
    if pt.status == 'paid':
        return redirect('order_success', order.order_number)
    context = {
        'order': order,
        'razorpay_order_id': pt.provider_order_id,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'amount': int(order.total * 100),
    }
    return render(request, 'payments/checkout.html', context)

@login_required
@require_POST
def ajax_create_checkout(request):
    address_id = request.POST.get('address_id')
    is_split = request.POST.get('is_split') == 'true'
    cart = Cart(request)
    
    if len(cart) == 0:
        return JsonResponse({'error': 'Cart is empty'}, status=400)
        
    try:
        address = Address.objects.get(id=address_id, user=request.user)
    except Address.DoesNotExist:
        return JsonResponse({'error': 'Invalid address'}, status=400)
        
    with transaction.atomic():
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
            
        cart.clear()
        
        # Trigger channels update
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        for item in order.items.all():
            async_to_sync(channel_layer.group_send)(
                f'product_{item.product.id}',
                {'type': 'purchase_update'}
            )
            
        if is_split:
            # Create a Razorpay order for 50% amount
            split_amount = order.total / 2
            # temporarily set order.total to split_amount for Razorpay order creation
            original_total = order.total
            order.total = split_amount
            rzp_id = PaymentService.create_razorpay_order(order)
            order.total = original_total
            
            # create split payment record
            from .models import SplitPayment
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
            
        if not rzp_id:
            return JsonResponse({'error': 'Could not initialize payment'}, status=500)
            
        return JsonResponse({
            'order_id': rzp_id,
            'amount': int(amount_to_pay * 100),
            'key': settings.RAZORPAY_KEY_ID,
            'our_order_number': order.order_number
        })

@csrf_exempt
@require_POST
def payment_verify(request):
    razorpay_payment_id = request.POST.get('razorpay_payment_id')
    razorpay_order_id = request.POST.get('razorpay_order_id')
    razorpay_signature = request.POST.get('razorpay_signature')
    is_ajax = request.POST.get('is_ajax') == 'true' or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if PaymentService.verify_payment_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
        with transaction.atomic():
            pt = get_object_or_404(PaymentTransaction, provider_order_id=razorpay_order_id)
            if pt.status != 'paid':
                pt.status = 'paid'
                pt.provider_payment_id = razorpay_payment_id
                pt.save()
                
                order = pt.order
                
                # Check for split payment
                from .models import SplitPayment
                split_payment = SplitPayment.objects.filter(order=order).first()
                
                if split_payment:
                    # If this is the primary payment (since is_paid is False and friend_user is None)
                    if not split_payment.is_paid and split_payment.friend_user is None:
                        order.status = 'pending'
                        order.payment_status = 'pending'  # still pending until friend pays
                        order.save()
                    else:
                        order.status = 'confirmed'
                        order.payment_status = 'completed'
                        order.save()
                        curate_mystery_box(order)
                else:
                    order.status = 'confirmed'
                    order.payment_status = 'completed'
                    order.save()
                    curate_mystery_box(order)
                
                # Clear cart
                cart = Cart(request)
                cart.clear()
                
                # Loyalty points
                if order.user and (not split_payment or split_payment.is_paid):
                    profile, _ = CustomerProfile.objects.get_or_create(user=order.user)
                    profile.lifetime_spent += order.total
                    profile.loyalty_points += int(order.total / 10)  # 1 point per 10 currency
                    profile.save()
                
                if not split_payment or split_payment.is_paid:
                    try:
                        EmailService.send_order_confirmation_email(order)
                    except Exception:
                        pass
        
        if is_ajax:
            return JsonResponse({'status': 'success', 'order_number': pt.order.order_number})
        return redirect('order_success', order_number=pt.order.order_number)
    else:
        if is_ajax:
            return JsonResponse({'error': 'Invalid Signature'}, status=400)
        return HttpResponseBadRequest("Invalid Signature")

@login_required
def friend_split_checkout(request, token):
    from .models import SplitPayment
    split_payment = get_object_or_404(SplitPayment, token=token)
    order = split_payment.order
    
    if split_payment.is_paid:
        messages.info(request, "This split payment has already been completed.")
        return redirect('order_success', order_number=order.order_number)
        
    if request.method == 'POST':
        original_total = order.total
        order.total = split_payment.amount_paid
        rzp_id = PaymentService.create_razorpay_order(order)
        order.total = original_total
        
        if rzp_id:
            split_payment.friend_user = request.user
            split_payment.save()
            context = {
                'order': order,
                'razorpay_order_id': rzp_id,
                'razorpay_key_id': settings.RAZORPAY_KEY_ID,
                'amount': int(split_payment.amount_paid * 100),
                'split_token': token
            }
            return render(request, 'payments/split_checkout.html', context)
        else:
            messages.error(request, "Could not initialize split payment.")
            
    return render(request, 'payments/split_checkout_prompt.html', {
        'split_payment': split_payment,
        'order': order
    })

@csrf_exempt
@require_POST
def split_payment_verify(request):
    token = request.POST.get('split_token')
    razorpay_payment_id = request.POST.get('razorpay_payment_id')
    razorpay_order_id = request.POST.get('razorpay_order_id')
    razorpay_signature = request.POST.get('razorpay_signature')
    
    from .models import SplitPayment
    split_payment = get_object_or_404(SplitPayment, token=token)
    
    if PaymentService.verify_payment_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
        with transaction.atomic():
            split_payment.is_paid = True
            split_payment.save()
            
            order = split_payment.order
            order.status = 'confirmed'
            order.payment_status = 'completed'
            order.save()
            curate_mystery_box(order)
            
            try:
                EmailService.send_order_confirmation_email(order)
            except Exception:
                pass
            
        return redirect('order_success', order_number=order.order_number)
    else:
        return HttpResponseBadRequest("Invalid Signature")
