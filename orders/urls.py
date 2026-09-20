from django.urls import path
from . import views
from . import ajax_views

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('checkout-ajax/', ajax_views.process_checkout_ajax, name='process_checkout_ajax'),
    path('success/<str:order_number>/', views.order_success, name='order_success'),
    path('group-buy/create/<int:product_id>/', views.create_group_buy, name='create_group_buy'),
    path('group-buy/<str:token>/', views.group_buy_detail, name='group_buy_detail'),
    path('mystery-box/reveal/<str:token>/', views.reveal_mystery_box, name='reveal_mystery_box'),
]
