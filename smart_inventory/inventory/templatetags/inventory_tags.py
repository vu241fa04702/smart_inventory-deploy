"""
Custom template tags for Smart Inventory Management System
"""

from django import template
from decimal import Decimal

register = template.Library()


@register.filter
def currency(value):
    """Format a value as currency"""
    try:
        return f'${float(value):,.2f}'
    except (ValueError, TypeError):
        return '$0.00'


@register.filter
def percentage(value):
    """Format a value as percentage"""
    try:
        return f'{float(value):.1f}%'
    except (ValueError, TypeError):
        return '0%'


@register.filter
def stock_badge(product):
    """Return Bootstrap badge class for stock status"""
    if product.stock_quantity == 0:
        return 'danger'
    elif product.is_low_stock:
        return 'warning'
    return 'success'


@register.filter
def stock_label(product):
    """Return stock status label"""
    if product.stock_quantity == 0:
        return 'Out of Stock'
    elif product.is_low_stock:
        return 'Low Stock'
    return 'In Stock'


@register.simple_tag
def sale_total(sale):
    """Calculate and return sale total"""
    return sale.total_amount


@register.filter
def multiply(value, arg):
    """Multiply two values"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0
