from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from mptt.models import MPTTModel, TreeForeignKey

class Category(MPTTModel):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    banner_image = models.ImageField(upload_to='categories/banners/', blank=True, null=True)
    icon = models.CharField(max_length=100, blank=True, null=True, help_text="Phosphor icon class, e.g. ph-laptop")
    
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)
    
    # SEO fields
    meta_title = models.CharField(max_length=200, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class MPTTMeta:
        order_insertion_by = ['display_order', 'name']
        
    class Meta:
        verbose_name_plural = 'Categories'
        
    def __str__(self):
        return self.name
        
    def clean(self):
        super().clean()
        if self.parent:
            # Enforce max depth of 3 (Level 0, 1, 2)
            # self.parent.level is 0 for Category, 1 for Subcategory. 
            # If parent is level 2, this would be level 3, which is not allowed.
            if self.parent.level >= 2:
                raise ValidationError("Categories cannot be nested deeper than 3 levels (Category -> Subcategory -> Child Category).")
            
            # Subcategory must have a parent that is a Category (level 0)
            # Child Category must have a parent that is a Subcategory (level 1)
            # This is inherently checked by the depth constraint above.
            
    @property
    def is_category(self):
        return self.level == 0
        
    @property
    def is_subcategory(self):
        return self.level == 1
        
    @property
    def is_child_category(self):
        return self.level == 2
