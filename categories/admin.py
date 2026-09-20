from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from .models import Category

class CategoryAdmin(MPTTModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    
admin.site.register(Category, CategoryAdmin)
