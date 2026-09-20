from django.contrib import admin
from .models import Lookbook, LookbookItem

class LookbookItemInline(admin.TabularInline):
    model = LookbookItem
    extra = 1

@admin.register(Lookbook)
class LookbookAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'created_at')
    prepopulated_fields = {'slug': ('title',)}
    list_filter = ('is_active',)
    search_fields = ('title',)
    inlines = [LookbookItemInline]

@admin.register(LookbookItem)
class LookbookItemAdmin(admin.ModelAdmin):
    list_display = ('lookbook', 'product', 'x_position', 'y_position')
    list_filter = ('lookbook',)
