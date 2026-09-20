from django.contrib import admin
from .models import PriceRule, PriceHistory

@admin.register(PriceRule)
class PriceRuleAdmin(admin.ModelAdmin):
    list_display = ('product', 'min_price', 'max_price')

@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'old_price', 'new_price', 'reason', 'created_at')
    readonly_fields = ('product', 'old_price', 'new_price', 'reason', 'created_at')
