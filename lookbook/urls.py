from django.urls import path
from . import views

app_name = 'lookbook'

urlpatterns = [
    path('', views.lookbook_index, name='index'),
    path('<slug:slug>/', views.lookbook_detail, name='detail'),
    path('builder/<int:pk>/', views.lookbook_builder, name='builder'),
    path('builder/<int:pk>/save/', views.lookbook_save_item, name='builder_save'),
    path('api/product-search/', views.lookbook_product_search, name='product_search'),
]
