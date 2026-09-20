import json
import os
from django.db.models import Q
from google import genai
from products.models import Product

def get_genai_client():
    api_key = os.environ.get('GEMINI_API_KEY')
    return genai.Client(api_key=api_key)

def search_products_db(query):
    products = Product.objects.filter(
        Q(name__icontains=query) | 
        Q(description__icontains=query) | 
        Q(category__name__icontains=query),
        status='published'
    ).distinct()[:5]
    
    result = []
    for p in products:
        img_url = ""
        img = p.images.filter(is_main=True).first()
        if not img:
            img = p.images.first()
        if img and img.image:
            img_url = img.image.url
            
        result.append({
            "id": p.id,
            "name": p.name,
            "price": float(p.price),
            "description": p.short_description or p.description[:100],
            "image_url": img_url,
            "url": f"/products/{p.slug}/"
        })
    return result

search_products_tool = {
    "type": "function",
    "name": "search_products",
    "description": "Searches for fashion products in the ecommerce database based on user query (e.g., 'summer shirt'). Returns a list of products with their ID, name, price, and image.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search term to look for"}
        },
        "required": ["query"]
    },
}

def process_chat_message(user_message, previous_interaction_id=None):
    client = get_genai_client()
    system_instruction = "You are a helpful AI Virtual Stylist for our e-commerce store. Use the search_products tool to find products the user is looking for and recommend them. Do not ask for size or color immediately unless they mention it, focus on recommending good matches. Format text with markdown."
    
    # Optional: we can configure store=True but we can also just use the memory of interaction
    interaction = client.interactions.create(
        model="gemini-3.8-flash",
        input=user_message,
        tools=[search_products_tool],
        previous_interaction_id=previous_interaction_id,
        system_instruction=system_instruction
    )
    
    product_payload = None
    
    # Process potential function calls
    for step in interaction.steps:
        if step.type == "function_call" and step.name == "search_products":
            # the step.arguments is a generic struct, sometimes it is a dict
            query = ""
            if hasattr(step, "arguments") and step.arguments:
                if isinstance(step.arguments, dict):
                    query = step.arguments.get("query", "")
                else:
                    query = getattr(step.arguments, "query", "")
                    
            products = search_products_db(query)
            product_payload = products
            
            # send result back to gemini
            interaction = client.interactions.create(
                model="gemini-3.8-flash",
                previous_interaction_id=interaction.id,
                input=[
                    {
                        "type": "function_result",
                        "call_id": step.id,
                        "name": step.name,
                        "result": [{"type": "text", "text": json.dumps(products)}],
                    }
                ],
                tools=[search_products_tool],
                system_instruction=system_instruction
            )
            break
            
    return {
        "text": interaction.output_text,
        "interaction_id": interaction.id,
        "products": product_payload
    }

from pydantic import BaseModel
from typing import List
from google.genai import types

class RecommendationResult(BaseModel):
    product_ids: List[int]
    explanation: str

def generate_homepage_recommendations(user_context):
    client = get_genai_client()
    
    # Fetch a sample of active products
    products_sample = list(Product.objects.filter(status='published').values('id', 'name', 'category__name')[:50])
    
    prompt = f"""
You are a personalized AI shopping assistant.
Based on the user's recent activity, recommend 3 to 4 products from the available catalog.
Provide a friendly, short explanation.

User Context:
{user_context}

Available Catalog (Sample):
{json.dumps(products_sample)}
"""
    
    response = client.models.generate_content(
        model='gemini-3.8-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=RecommendationResult,
        )
    )
    return response.text
