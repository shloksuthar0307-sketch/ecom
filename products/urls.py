from django.urls import path
from . import views

urlpatterns = [
    path('', views.shop_view, name='shop'),
    path('compare/', views.compare_view, name='compare'),
    path('<slug:slug>/', views.product_detail, name='product_detail'),
    path('<slug:slug>/quick-view/', views.quick_view, name='quick_view'),
    path('<int:product_id>/review/', views.add_review, name='add_review'),
]

