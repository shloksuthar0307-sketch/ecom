from django.urls import path
from . import views

app_name = 'gifts'

urlpatterns = [
    path('gift-studio/', views.gift_studio, name='studio'),
    path('api/gift/save/', views.save_gift_config, name='save_config'),
    path('api/gift/signature/', views.generate_signature, name='signature'),
    path('gift/message/<str:qr_token>/', views.recipient_page, name='recipient'),
]
