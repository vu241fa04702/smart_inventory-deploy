"""
Models for Smart Inventory Management System
Includes: Category, Product, Sale, SaleItem
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal


class Category(models.Model):
    """Product category model"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def product_count(self):
        return self.products.count()


class Product(models.Model):
    """Product model with stock tracking"""
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True, help_text='Stock Keeping Unit')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text='Selling price')
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Purchase/cost price')
    stock_quantity = models.IntegerField(default=0, help_text='Current stock level')
    low_stock_threshold = models.IntegerField(default=10, help_text='Alert when stock falls below this')
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name} (SKU: {self.sku})'

    @property
    def is_low_stock(self):
        """Check if product is below the low stock threshold"""
        return self.stock_quantity <= self.low_stock_threshold

    @property
    def profit_margin(self):
        """Calculate profit margin percentage"""
        if self.price > 0:
            return round(((self.price - self.cost_price) / self.price) * 100, 2)
        return 0

    @property
    def stock_value(self):
        """Calculate total value of current stock"""
        return self.stock_quantity * self.cost_price


class Sale(models.Model):
    """Sale transaction model"""
    STATUS_CHOICES = [
        ('completed', 'Completed'),
        ('pending', 'Pending'),
        ('cancelled', 'Cancelled'),
    ]

    sale_number = models.CharField(max_length=20, unique=True)
    customer_name = models.CharField(max_length=200, blank=True, default='Walk-in Customer')
    customer_email = models.EmailField(blank=True, null=True)
    customer_phone = models.CharField(max_length=20, blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Sale #{self.sale_number} - {self.customer_name}'

    @property
    def subtotal(self):
        """Calculate sale subtotal before discount"""
        return sum(item.total_price for item in self.items.all())

    @property
    def total_amount(self):
        """Calculate total amount"""
        return self.subtotal

    @property
    def total_items(self):
        """Count total items in this sale"""
        return sum(item.quantity for item in self.items.all())

    def save(self, *args, **kwargs):
        """Auto-generate sale number if not set"""
        if not self.sale_number:
            last_sale = Sale.objects.order_by('-id').first()
            next_id = (last_sale.id + 1) if last_sale else 1
            self.sale_number = f'SALE-{next_id:05d}'
        super().save(*args, **kwargs)


class SaleItem(models.Model):
    """Individual items within a sale"""
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='sale_items')
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, help_text='Price at time of sale')
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text='Discount percentage')

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'

    @property
    def total_price(self):
        """Calculate total price after discount"""
        base_total = self.unit_price * self.quantity
        discount_amount = base_total * (self.discount / 100)
        return base_total - discount_amount

    def save(self, *args, **kwargs):
        """Auto-set unit price from product if not set"""
        if not self.unit_price:
            self.unit_price = self.product.price
        super().save(*args, **kwargs)


class StockMovement(models.Model):
    """Track all stock movements for audit purposes"""
    MOVEMENT_TYPES = [
        ('sale', 'Sale'),
        ('purchase', 'Purchase'),
        ('adjustment', 'Manual Adjustment'),
        ('return', 'Return'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity_change = models.IntegerField(help_text='Positive = stock in, Negative = stock out')
    quantity_before = models.IntegerField()
    quantity_after = models.IntegerField()
    reference = models.CharField(max_length=50, blank=True, null=True, help_text='Sale number or PO number')
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.product.name} - {self.movement_type} ({self.quantity_change:+d})'
