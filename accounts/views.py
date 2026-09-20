from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Address, CustomerProfile, LoyaltyTransaction

@login_required
def account_dashboard(request):
    addresses = request.user.addresses.all()
    profile, created = CustomerProfile.objects.get_or_create(user=request.user)
    transactions = request.user.loyalty_transactions.all().order_by('-created_at')[:5]
    
    if request.method == 'POST':
        # Simple address creation
        Address.objects.create(
            user=request.user,
            title=request.POST.get('title', 'Home'),
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            phone=request.POST.get('phone'),
            street_address=request.POST.get('street_address'),
            city=request.POST.get('city'),
            state=request.POST.get('state'),
            postal_code=request.POST.get('postal_code'),
            country=request.POST.get('country')
        )
        messages.success(request, "Address added successfully.")
        return redirect('account_dashboard')
        
    context = {
        'addresses': addresses,
        'profile': profile,
        'transactions': transactions,
    }
    return render(request, 'accounts/dashboard.html', context)
@login_required
def account_orders(request):
    orders = request.user.orders.all().order_by('-created_at')
    return render(request, 'accounts/orders.html', {'orders': orders})

from django.contrib.auth import login
from .forms import CustomUserCreationForm
from core.services.email_service import EmailService
from django.contrib.sites.shortcuts import get_current_site

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            
            # Send Welcome Email
            try:
                # We can't rely on site_url in background tasks easily if not passed, but let's pass a basic one
                EmailService.send_welcome_email(user)
            except Exception as e:
                pass # Fail silently so user isn't blocked
                
            messages.success(request, "Registration successful. Welcome!")
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})
