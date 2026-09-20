from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from products.models import Product
from categories.models import Category

class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'daily'

    def items(self):
        return ['home', 'about', 'shop']

    def location(self, item):
        return reverse(item)

class ProductSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.9

    def items(self):
        return Product.objects.filter(status='published')

    def lastmod(self, obj):
        return obj.updated_at
        
    def location(self, obj):
        return reverse('product_detail', args=[obj.slug])

class CategorySitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        return Category.objects.all()

    def location(self, obj):
        return reverse('category_detail', args=[obj.slug])
