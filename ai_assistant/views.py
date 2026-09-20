import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .services import process_chat_message

@csrf_exempt
@require_POST
def chat_api(request):
    try:
        data = json.loads(request.body)
        user_message = data.get("message")
        
        if not user_message:
            return JsonResponse({"error": "Message is required"}, status=400)
            
        # Get previous interaction ID from session
        previous_interaction_id = request.session.get("gemini_interaction_id")
        
        # Call Gemini service
        result = process_chat_message(user_message, previous_interaction_id)
        
        # Save the interaction ID for the next turn
        request.session["gemini_interaction_id"] = result["interaction_id"]
        
        # Append to chat history in session for frontend persistence if needed
        chat_history = request.session.get("chat_history", [])
        chat_history.append({"role": "user", "text": user_message})
        chat_history.append({"role": "assistant", "text": result["text"]})
        request.session["chat_history"] = chat_history
        
        return JsonResponse({
            "text": result["text"],
            "products": result["products"] or []
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)

from django.shortcuts import render
from products.models import Product
from google import genai
from google.genai import types

def ai_search(request):
    query = request.GET.get('q', '')
    if not query:
        return render(request, 'ai_assistant/results.html', {'error': 'No query provided.', 'query': query})
        
    try:
        from pydantic import BaseModel, Field
        from typing import List, Optional
        
        class PriceRange(BaseModel):
            min: Optional[float] = None
            max: Optional[float] = None
            
        class SearchIntent(BaseModel):
            intent: str = Field(description="General intent of the query")
            keywords: List[str]
            categories: List[str]
            brands: List[str]
            price_range: Optional[PriceRange] = None
            features: List[str]
            sort_preference: Optional[str] = Field(description="e.g. price_low, price_high, newest")

        client = genai.Client()
        prompt = f"""Extract search intent from this query: "{query}".
Do not hallucinate products."""
        interaction = client.interactions.create(
            model='gemini-3.8-flash',
            input=prompt,
            response_format=[
                {
                    "type": "text",
                    "mime_type": "application/json",
                    "schema": SearchIntent.model_json_schema(),
                }
            ],
        )
        response_text = interaction.output_text.strip()
        intent = json.loads(response_text)
        
        products = Product.objects.filter(status='published', visibility='visible')
        
        from django.db.models import Q
        
        if intent.get('categories'):
            category_q = Q()
            for cat in intent['categories']:
                category_q |= Q(category__name__icontains=cat)
            products = products.filter(category_q)
            
        if intent.get('brands'):
            brand_q = Q()
            for brand in intent['brands']:
                brand_q |= Q(brand__name__icontains=brand)
            products = products.filter(brand_q)
            
        if intent.get('price_range'):
            pr = intent['price_range']
            if pr.get('min') is not None:
                products = products.filter(price__gte=pr['min'])
            if pr.get('max') is not None:
                products = products.filter(price__lte=pr['max'])
                
        if intent.get('keywords') or intent.get('features'):
            terms = (intent.get('keywords') or []) + (intent.get('features') or [])
            for term in terms:
                products = products.filter(
                    Q(name__icontains=term) | 
                    Q(description__icontains=term) | 
                    Q(short_description__icontains=term) |
                    Q(variants__attributes__icontains=term)
                ).distinct()
                
        if intent.get('sort_preference'):
            if intent['sort_preference'] == 'price_low':
                products = products.order_by('price')
            elif intent['sort_preference'] == 'price_high':
                products = products.order_by('-price')
            else:
                products = products.order_by('-created_at')
            
    except Exception as e:
        # Graceful fallback
        intent = {}
        products = Product.objects.filter(name__icontains=query, status='published', visibility='visible')
        
    return render(request, 'ai_assistant/results.html', {
        'products': products.distinct(),
        'query': query,
        'intent': intent
    })
