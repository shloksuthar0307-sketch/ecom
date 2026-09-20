from django.db import models
from categories.models import Category

class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    )
    
    VISIBILITY_CHOICES = (
        ('visible', 'Visible'),
        ('hidden', 'Hidden'),
    )
    
    STOCK_STATUS_CHOICES = (
        ('in_stock', 'In Stock'),
        ('low_stock', 'Low Stock'),
        ('out_of_stock', 'Out of Stock'),
    )

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    sku = models.CharField(max_length=100, unique=True)
    short_description = models.TextField(blank=True, null=True)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tax = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Tax percentage")
    
    stock_quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    stock_status = models.CharField(max_length=20, choices=STOCK_STATUS_CHOICES, default='in_stock')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='visible')
    
    is_featured = models.BooleanField(default=False)
    is_bestseller = models.BooleanField(default=False)
    is_new_arrival = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    views_count = models.PositiveIntegerField(default=0)
    
    is_mystery_box = models.BooleanField(default=False, help_text="Designates this product as a mystery box")
    tags = models.CharField(max_length=255, blank=True, null=True, help_text="Comma-separated tags for AI curation matching")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
        
    def get_root_category(self):
        # Returns the Level 0 Category
        ancestors = self.category.get_ancestors(include_self=True)
        return ancestors.filter(level=0).first()
        
    def get_subcategory(self):
        # Returns the Level 1 Category
        ancestors = self.category.get_ancestors(include_self=True)
        return ancestors.filter(level=1).first()
        
    def get_child_category(self):
        # Returns the Level 2 Category
        ancestors = self.category.get_ancestors(include_self=True)
        return ancestors.filter(level=2).first()

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=255, blank=True, null=True)
    is_main = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Image for {self.product.name}"

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    name = models.CharField(max_length=100, help_text="e.g. Red / Large")
    sku = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Override product price")
    stock = models.PositiveIntegerField(default=0)
    image = models.ForeignKey(ProductImage, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Store attributes flexibly. For simplicity without Postgres JSONB, we'll use a separate model or simple structure.
    # In a real app we might use JSONField or an EAV (Entity-Attribute-Value) model. 
    # Since Postgres is required for prod, let's use Django's JSONField which is standard now.
    attributes = models.JSONField(default=dict, help_text="e.g. {'Size': 'L', 'Color': 'Red'}")

    def __str__(self):
        return f"{self.product.name} - {self.name}"

class Review(models.Model):
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey('accounts.User', related_name='reviews', on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('product', 'user') # One review per user per product
        
    def __str__(self):
        return f"{self.user.email} - {self.product.name} - {self.rating} Stars"

class ReviewMedia(models.Model):
    MEDIA_TYPES = (
        ('image', 'Image'),
        ('video', 'Video'),
    )
    review = models.ForeignKey(Review, related_name='media', on_delete=models.CASCADE)
    file = models.FileField(upload_to='reviews/media/')
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES, default='image')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.media_type} for Review {self.review.id}"

