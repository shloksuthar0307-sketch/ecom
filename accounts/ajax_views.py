from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .models import Address
import json

@login_required
@require_POST
def add_address_ajax(request):
    try:
        data = json.loads(request.body)
        addr = Address.objects.create(
            user=request.user,
            title=data.get('title', 'Home'),
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            phone=data.get('phone'),
            street_address=data.get('street_address'),
            apartment_address=data.get('apartment_address', ''),
            city=data.get('city'),
            state=data.get('state'),
            postal_code=data.get('postal_code'),
            country=data.get('country')
        )
        return JsonResponse({'success': True, 'id': addr.id, 'title': addr.title, 'text': f"{addr.first_name} {addr.last_name}, {addr.street_address}, {addr.city}"})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
