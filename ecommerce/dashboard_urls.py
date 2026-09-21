from django.urls import path
from core import admin_views as core_admin
from categories import admin_views as cat_admin
from products import admin_views as prod_admin

urlpatterns = [
    path('', core_admin.custom_dashboard, name='custom_dashboard'),
    
    # Categories
    path('categories/', cat_admin.category_list, name='dashboard_category_list'),
    path('categories/add/<int:level>/', cat_admin.category_add, name='dashboard_category_add'),
    path('categories/edit/<int:pk>/', cat_admin.category_edit, name='dashboard_category_edit'),
    path('categories/delete/<int:pk>/', cat_admin.category_delete, name='dashboard_category_delete'),
    path('categories/ajax/load-subcategories/', cat_admin.ajax_load_subcategories, name='ajax_load_subcategories'),
    
    # Products
    path('products/', prod_admin.product_list, name='dashboard_products'),
    path('products/add/', prod_admin.product_add, name='add_product'),
    path('products/edit/<int:pk>/', prod_admin.product_edit, name='edit_product'),
    path('products/delete/<int:pk>/', prod_admin.product_delete, name='delete_product'),
    
    # API
    path('api/analytics/', core_admin.analytics_data, name='api_analytics'),
    path('api/categories/<int:parent_id>/children/', prod_admin.get_child_categories, name='api_get_child_categories'),
]
