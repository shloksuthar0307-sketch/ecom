from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import index, about
from core import admin_views as core_admin_views
from products import views as products_views

from django.contrib.sitemaps.views import sitemap
from core.sitemaps import StaticViewSitemap, ProductSitemap, CategorySitemap
from django.views.generic import TemplateView

sitemaps = {
    'static': StaticViewSitemap,
    'products': ProductSitemap,
    'categories': CategorySitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='home'),
    path('about/', about, name='about'),
    path('dashboard/', include('ecommerce.dashboard_urls')),
    path('search/', include([
        path('', products_views.search_view, name='search'),
        path('suggestions/', products_views.search_suggestions, name='search_suggestions'),
    ])),
    path('payments/', include('payments.urls')),
    path('shop/', include('products.urls')),
    path('categories/', include('categories.urls')),
    path('account/', include('accounts.urls')),
    path('cart/', include('cart.urls')),
    path('wishlist/', include('wishlist.urls')),
    path('orders/', include('orders.urls')),
    path('lookbook/', include('lookbook.urls')),
    path('ai/', include('ai_assistant.urls')),
    path('auctions/', include('auctions.urls')),
    path('', include('gifts.urls')),
    
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
