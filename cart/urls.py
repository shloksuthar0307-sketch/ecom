from django.urls import path
from . import views
from . import ajax_views

urlpatterns = [
    path('', views.cart_detail, name='cart_detail'),
    path('add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('update/<int:item_id>/', views.cart_update, name='cart_update'),
    path('remove/<int:item_id>/', views.cart_remove, name='cart_remove'),
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('apply-coupon-ajax/', ajax_views.apply_coupon_ajax, name='apply_coupon_ajax'),
    path('recommendations-ajax/', ajax_views.get_cart_recommendations, name='get_cart_recommendations'),
]
