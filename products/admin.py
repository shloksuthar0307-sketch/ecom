from django.contrib import admin
from .models import Brand, Product, ProductImage, ProductVariant, Review, ReviewMedia

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class ProductVariantInline(admin.StackedInline):
    model = ProductVariant
    extra = 1

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'price', 'stock_quantity', 'status', 'is_featured')
    list_filter = ('status', 'is_featured', 'category', 'brand')
    search_fields = ('name', 'sku')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ProductVariantInline]

class BrandAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

class ReviewMediaInline(admin.TabularInline):
    model = ReviewMedia
    extra = 1

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'is_verified', 'is_approved', 'created_at')
    list_filter = ('is_verified', 'is_approved', 'rating', 'created_at')
    search_fields = ('product__name', 'user__email', 'comment')
    actions = ['approve_reviews', 'hide_reviews']
    inlines = [ReviewMediaInline]

    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
    approve_reviews.short_description = "Approve selected reviews"

    def hide_reviews(self, request, queryset):
        queryset.update(is_approved=False)
    hide_reviews.short_description = "Hide selected reviews"

admin.site.register(Brand, BrandAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Review, ReviewAdmin)
