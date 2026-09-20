from django.urls import path
from . import views

urlpatterns = [
    path('', views.wishlist_detail, name='wishlist_detail'),
    path('toggle/<int:product_id>/', views.wishlist_toggle, name='wishlist_toggle'),
]
