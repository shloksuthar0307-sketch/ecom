from decimal import Decimal
from django.db import transaction
from .models import PriceRule, PriceHistory

def calculate_dynamic_price(product):
    """
    Adjusts the product price based on views_count.
    Increases price if views_count is high, capped at PriceRule.max_price.
    """
    try:
        rule = product.price_rule
    except PriceRule.DoesNotExist:
        # No dynamic pricing rule for this product
        return

    # Base price calculation logic based on views
    # E.g., for every 10 views, increase price by 1% of the base/min price.
    # Just an arbitrary "demand" algorithm
    increase_factor = product.views_count // 10
    if increase_factor <= 0:
        return
        
    increase_amount = Decimal('0.01') * rule.min_price * increase_factor
    calculated_price = rule.min_price + increase_amount

    # Cap at max_price
    new_price = min(calculated_price, rule.max_price)

    # Only update if the new price is different from the current price
    # (assuming product.price is the current price)
    if product.price != new_price:
        old_price = product.price
        
        with transaction.atomic():
            product.price = new_price
            product.save(update_fields=['price'])
            
            PriceHistory.objects.create(
                product=product,
                old_price=old_price,
                new_price=new_price,
                reason=f"High demand due to {product.views_count} views."
            )
