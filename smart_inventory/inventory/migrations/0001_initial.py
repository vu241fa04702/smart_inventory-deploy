"""
Initial database migration for Smart Inventory Management System
Generated migration - creates all tables
"""

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Category',
                'verbose_name_plural': 'Categories',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('sku', models.CharField(help_text='Stock Keeping Unit', max_length=50, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('price', models.DecimalField(decimal_places=2, help_text='Selling price', max_digits=10)),
                ('cost_price', models.DecimalField(decimal_places=2, default=0, help_text='Purchase/cost price', max_digits=10)),
                ('stock_quantity', models.IntegerField(default=0, help_text='Current stock level')),
                ('low_stock_threshold', models.IntegerField(default=10, help_text='Alert when stock falls below this')),
                ('image', models.ImageField(blank=True, null=True, upload_to='products/')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='products', to='inventory.category')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Sale',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sale_number', models.CharField(max_length=20, unique=True)),
                ('customer_name', models.CharField(blank=True, default='Walk-in Customer', max_length=200)),
                ('customer_email', models.EmailField(blank=True, null=True)),
                ('customer_phone', models.CharField(blank=True, max_length=20, null=True)),
                ('status', models.CharField(choices=[('completed', 'Completed'), ('pending', 'Pending'), ('cancelled', 'Cancelled')], default='completed', max_length=20)),
                ('notes', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='SaleItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField(default=1)),
                ('unit_price', models.DecimalField(decimal_places=2, help_text='Price at time of sale', max_digits=10)),
                ('discount', models.DecimalField(decimal_places=2, default=0, help_text='Discount percentage', max_digits=5)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='sale_items', to='inventory.product')),
                ('sale', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='inventory.sale')),
            ],
        ),
        migrations.CreateModel(
            name='StockMovement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('movement_type', models.CharField(choices=[('sale', 'Sale'), ('purchase', 'Purchase'), ('adjustment', 'Manual Adjustment'), ('return', 'Return')], max_length=20)),
                ('quantity_change', models.IntegerField(help_text='Positive = stock in, Negative = stock out')),
                ('quantity_before', models.IntegerField()),
                ('quantity_after', models.IntegerField()),
                ('reference', models.CharField(blank=True, help_text='Sale number or PO number', max_length=50, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='movements', to='inventory.product')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
