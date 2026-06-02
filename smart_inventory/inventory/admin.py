"""
Admin panel customization for Smart Inventory Management System
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, Sale, SaleItem, StockMovement

# Customize admin site header
admin.site.site_header = 'Smart Inventory Admin'
admin.site.site_title = 'Inventory Admin'
admin.site.index_title = 'Welcome to Smart Inventory Management'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'product_count', 'created_at']
    search_fields = ['name']

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'category', 'price', 'stock_quantity', 'stock_status', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'sku', 'description']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['is_active']

    def stock_status(self, obj):
        if obj.stock_quantity == 0:
            return format_html('<span style="color:red; font-weight:bold">Out of Stock</span>')
        elif obj.is_low_stock:
            return format_html('<span style="color:orange; font-weight:bold">Low Stock</span>')
        return format_html('<span style="color:green">In Stock</span>')
    stock_status.short_description = 'Stock Status'


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ['total_price']


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['sale_number', 'customer_name', 'total_amount', 'status', 'created_by', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['sale_number', 'customer_name', 'customer_email']
    readonly_fields = ['sale_number', 'created_at', 'updated_at']
    inlines = [SaleItemInline]


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['product', 'movement_type', 'quantity_change', 'quantity_before', 'quantity_after', 'created_at']
    list_filter = ['movement_type', 'created_at']
    search_fields = ['product__name', 'reference']
    readonly_fields = ['created_at']
