from django.urls import path
from . import views

urlpatterns = [
    path('checkout/<str:order_number>/', views.payment_checkout, name='payment_checkout'),
    path('verify/', views.payment_verify, name='payment_verify'),
    path('webhook/', views.razorpay_webhook, name='razorpay_webhook'),
    path('ajax-checkout/', views.ajax_create_checkout, name='ajax_checkout'),
    path('split/<str:token>/', views.friend_split_checkout, name='friend_split_checkout'),
    path('split-verify/', views.split_payment_verify, name='split_payment_verify'),
]
