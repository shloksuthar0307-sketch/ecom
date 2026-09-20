import json
import uuid
import os
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import List
from django.db.models import Q
from .models import MysteryBox, OrderItem
from products.models import Product

class MysteryPreferences(BaseModel):
    preferred_tags: List[str]
    preferred_categories: List[str]

def get_genai_client():
    api_key = os.environ.get('GEMINI_API_KEY')
    return genai.Client(api_key=api_key)

def curate_mystery_box(order):
    mystery_items = order.items.filter(product__is_mystery_box=True)
    if not mystery_items.exists():
        return
        
    client = get_genai_client()
    user = order.user
    
    # Gather user context
    past_purchases = list(OrderItem.objects.filter(
        order__user=user, 
        order__payment_status='completed'
    ).values_list('product_name', flat=True).distinct()[:20])
    
    wishlist_products = []
    try:
        if hasattr(user, 'wishlist'):
            wishlist_products = list(user.wishlist.products.values_list('name', flat=True)[:20])
    except Exception:
        pass
        
    prompt = f"""
    You are an AI curator for a Mystery Box.
    User's Past Purchases: {past_purchases}
    User's Wishlist: {wishlist_products}
    
    Based on this, suggest preferred categories and tags for products they would like.
    """
    
    preferred_tags = []
    preferred_categories = []
    
    try:
        response = client.models.generate_content(
            model='gemini-3.8-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=MysteryPreferences,
            )
        )
        prefs = json.loads(response.text)
        preferred_tags = prefs.get('preferred_tags', [])
        preferred_categories = prefs.get('preferred_categories', [])
    except Exception as e:
        # Fallback if API fails
        pass

    # Build DB Query for matching products
    query = Q(stock_status='in_stock', is_mystery_box=False)
    
    # If we got preferences, filter by them
    if preferred_categories or preferred_tags:
        pref_query = Q()
        for cat in preferred_categories:
            pref_query |= Q(category__name__icontains=cat)
        for tag in preferred_tags:
            pref_query |= Q(tags__icontains=tag) | Q(name__icontains=tag) | Q(description__icontains=tag)
            
        # Combine base query with preferences
        matched_products = Product.objects.filter(query & pref_query).distinct().order_by('?')
        if not matched_products.exists():
            matched_products = Product.objects.filter(query).order_by('?')
    else:
        matched_products = Product.objects.filter(query).order_by('?')

    # Create boxes and add products
    for item in mystery_items:
        # Mystery box value logic: If they paid X, give them value of at least 1.4 * X
        # The prompt mentioned "e.g., 5000" and "value promise >= 7000". We'll just aim for > 1.4 * price
        target_value = float(item.price) * 1.4
        
        selected_products = []
        current_value = 0.0
        
        for p in matched_products:
            if current_value >= target_value:
                break
            # To avoid selecting same product twice in one box
            if p not in selected_products:
                selected_products.append(p)
                current_value += float(p.price)
                
        # If we couldn't reach target value, just give what we found or fallback to randomly adding more
        if current_value < target_value:
            more_products = Product.objects.filter(query).exclude(id__in=[p.id for p in selected_products]).order_by('?')
            for p in more_products:
                if current_value >= target_value:
                    break
                selected_products.append(p)
                current_value += float(p.price)
                
        # Create MysteryBox
        box = MysteryBox.objects.create(
            order_item=item,
            token=str(uuid.uuid4())
        )
        box.products.set(selected_products)
