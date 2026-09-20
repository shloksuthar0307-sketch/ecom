from django.urls import path
from . import views

urlpatterns = [
    # Frontend endpoints
    path('', views.category_list, name='category_list'),
    path('<slug:category_slug>/', views.category_detail, name='category_detail'),
    path('<slug:category_slug>/<slug:subcategory_slug>/', views.subcategory_detail, name='subcategory_detail'),
    path('<slug:category_slug>/<slug:subcategory_slug>/<slug:child_slug>/', views.child_category_detail, name='child_category_detail'),
]
