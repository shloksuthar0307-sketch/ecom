from django.contrib import admin
from .models import Coupon

class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'active', 'start_date', 'expiry_date')
    list_filter = ('active', 'discount_type')
    search_fields = ('code',)

admin.site.register(Coupon, CouponAdmin)
