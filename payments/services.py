import razorpay
from django.conf import settings
from .models import PaymentTransaction

class PaymentService:
    @staticmethod
    def get_client():
        return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    @staticmethod
    def create_razorpay_order(order):
        client = PaymentService.get_client()
        # amount is in paise
        amount = int(order.total * 100)
        data = {
            "amount": amount,
            "currency": "INR",
            "receipt": f"receipt_{order.order_number}"
        }
        try:
            payment = client.order.create(data=data)
            
            # Record the transaction
            PaymentTransaction.objects.update_or_create(
                order=order,
                defaults={
                    'provider': 'razorpay',
                    'provider_order_id': payment['id'],
                    'amount': order.total,
                    'currency': 'INR',
                    'status': 'pending'
                }
            )
            return payment['id']
        except Exception as e:
            # Handle API errors
            return None
        
    @staticmethod
    def verify_payment_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
        client = PaymentService.get_client()
        try:
            return client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            })
        except razorpay.errors.SignatureVerificationError:
            return False
