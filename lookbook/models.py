from django.db import models
from products.models import Product

class Lookbook(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    hero_image = models.ImageField(upload_to='lookbooks/')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class LookbookItem(models.Model):
    lookbook = models.ForeignKey(Lookbook, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='lookbook_items')
    x_position = models.FloatField(help_text="X position in percentage (0-100)")
    y_position = models.FloatField(help_text="Y position in percentage (0-100)")

    def __str__(self):
        return f"{self.product.name} in {self.lookbook.title}"
