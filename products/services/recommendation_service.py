from django.db.models import Count, Q, Value, IntegerField
from django.db.models.functions import Coalesce
from products.models import Product

class RecommendationService:
    @staticmethod
    def get_related_products(product, limit=4):
        # Annotate all other published products with a recommendation score
        # Base query
        queryset = Product.objects.filter(status='published').exclude(id=product.id)
        
        # Build conditional expressions for algorithmic scoring
        # 1. Match Child Category (+50)
        # 2. Match Subcategory (+30)
        # 3. Match Root Category (+10)
        # 4. Same Brand (+20)
        # 5. Add order count directly to score
        from django.db.models import Case, When
        
        scoring_conditions = []
        
        # Child Category Match
        if product.category.level == 2:
            scoring_conditions.append(
                When(category=product.category, then=Value(50))
            )
            scoring_conditions.append(
                When(category__in=product.category.parent.get_descendants(), then=Value(30))
            )
        elif product.category.level == 1:
            scoring_conditions.append(
                When(category__in=product.category.get_descendants(include_self=True), then=Value(40))
            )
            
        scoring_conditions.append(
            When(category__in=product.get_root_category().get_descendants(include_self=True), then=Value(10))
        )
            
        score_expression = Case(
            *scoring_conditions,
            default=Value(0),
            output_field=IntegerField()
        )
        
        if product.brand:
            score_expression += Case(
                When(brand=product.brand, then=Value(20)),
                default=Value(0),
                output_field=IntegerField()
            )
        
        # Add order count for popularity score (approximate popularity: +1 for each order item, capped or simply added)
        # We'll just add the raw order count to the score.
        queryset = queryset.annotate(
            order_count=Count('orderitem'),
            rec_score=score_expression
        ).annotate(
            final_score=Coalesce('rec_score', Value(0)) + Coalesce('order_count', Value(0))
        ).order_by('-final_score', '-created_at')[:limit]
        
        return list(queryset)

    @staticmethod
    def get_frequently_bought_together(product, limit=4):
        # Look at orders containing this product, find what else was in those orders
        order_ids = product.orderitem_set.values_list('order_id', flat=True)
        if not order_ids:
            return RecommendationService.get_related_products(product, limit)
            
        freq_products = Product.objects.filter(
            status='published',
            orderitem__order__id__in=order_ids
        ).exclude(id=product.id).annotate(
            purchase_count=Count('orderitem')
        ).order_by('-purchase_count')[:limit]
        
        if len(freq_products) < limit:
            # Fallback to fill
            needed = limit - len(freq_products)
            exclude_ids = [p.id for p in freq_products] + [product.id]
            fallback = Product.objects.filter(status='published', category=product.category).exclude(id__in=exclude_ids)[:needed]
            freq_products = list(freq_products) + list(fallback)
            
        return list(freq_products)
