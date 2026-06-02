"""
Management command to populate the database with sample data.
Run: python manage.py populate_sample_data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
import random

from inventory.models import Category, Product, Sale, SaleItem, StockMovement


class Command(BaseCommand):
    help = 'Populate database with sample data for demonstration'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating sample data...'))

        # Create superuser admin
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@smartinventory.com',
                password='admin123',
                first_name='Admin',
                last_name='User'
            )
            self.stdout.write(self.style.SUCCESS('  ✓ Created admin user (admin / admin123)'))
        else:
            admin = User.objects.get(username='admin')
            self.stdout.write('  → Admin user already exists')

        # Create demo user
        if not User.objects.filter(username='demo').exists():
            demo_user = User.objects.create_user(
                username='demo',
                email='demo@smartinventory.com',
                password='demo123',
                first_name='Demo',
                last_name='Manager'
            )
            self.stdout.write(self.style.SUCCESS('  ✓ Created demo user (demo / demo123)'))
        else:
            demo_user = User.objects.get(username='demo')

        # Create categories
        categories_data = [
            ('Electronics', 'Electronic devices and accessories'),
            ('Clothing', 'Apparel and fashion items'),
            ('Food & Beverages', 'Consumable food and drink products'),
            ('Home & Garden', 'Home décor and gardening supplies'),
            ('Sports & Fitness', 'Sports equipment and fitness gear'),
            ('Books & Media', 'Books, music, and digital media'),
            ('Toys & Games', 'Children toys and board games'),
            ('Health & Beauty', 'Personal care and health products'),
        ]

        categories = {}
        for name, desc in categories_data:
            cat, created = Category.objects.get_or_create(name=name, defaults={'description': desc})
            categories[name] = cat
            if created:
                self.stdout.write(f'  ✓ Created category: {name}')

        # Create products
        products_data = [
            # Electronics
            ('Wireless Headphones', 'WH-001', 'Electronics', 79.99, 45.00, 35, 8),
            ('Bluetooth Speaker', 'BS-002', 'Electronics', 49.99, 28.00, 50, 10),
            ('USB-C Hub', 'UC-003', 'Electronics', 34.99, 18.00, 25, 5),
            ('Laptop Stand', 'LS-004', 'Electronics', 29.99, 15.00, 40, 8),
            ('Wireless Mouse', 'WM-005', 'Electronics', 24.99, 12.00, 60, 10),
            ('Mechanical Keyboard', 'MK-006', 'Electronics', 89.99, 52.00, 20, 5),
            ('Webcam HD', 'WC-007', 'Electronics', 59.99, 35.00, 3, 5),  # Low stock
            ('Smart Watch', 'SW-008', 'Electronics', 199.99, 110.00, 15, 10),

            # Clothing
            ('Cotton T-Shirt', 'CT-009', 'Clothing', 19.99, 8.00, 100, 20),
            ('Denim Jeans', 'DJ-010', 'Clothing', 49.99, 22.00, 75, 15),
            ('Winter Jacket', 'WJ-011', 'Clothing', 89.99, 48.00, 30, 8),
            ('Running Shoes', 'RS-012', 'Clothing', 69.99, 38.00, 0, 10),  # Out of stock

            # Food & Beverages
            ('Green Tea Box', 'GT-013', 'Food & Beverages', 12.99, 6.00, 200, 30),
            ('Protein Bars (12pk)', 'PB-014', 'Food & Beverages', 24.99, 14.00, 80, 20),
            ('Coffee Beans 1kg', 'CB-015', 'Food & Beverages', 18.99, 10.00, 45, 15),
            ('Vitamin C Supplements', 'VC-016', 'Food & Beverages', 15.99, 8.50, 7, 10),  # Low stock

            # Home & Garden
            ('Scented Candle Set', 'SC-017', 'Home & Garden', 22.99, 11.00, 55, 10),
            ('Plant Pot Set', 'PP-018', 'Home & Garden', 16.99, 8.00, 40, 8),
            ('LED Desk Lamp', 'DL-019', 'Home & Garden', 39.99, 20.00, 25, 5),
            ('Kitchen Organizer', 'KO-020', 'Home & Garden', 28.99, 14.00, 18, 5),

            # Sports & Fitness
            ('Yoga Mat', 'YM-021', 'Sports & Fitness', 29.99, 15.00, 35, 8),
            ('Resistance Bands Set', 'RB-022', 'Sports & Fitness', 19.99, 9.00, 60, 10),
            ('Water Bottle 1L', 'WB-023', 'Sports & Fitness', 14.99, 7.00, 90, 15),
            ('Jump Rope', 'JR-024', 'Sports & Fitness', 9.99, 4.00, 4, 8),  # Low stock

            # Books & Media
            ('Python Programming Book', 'PPB-025', 'Books & Media', 34.99, 18.00, 25, 5),
            ('Business Strategy Guide', 'BSG-026', 'Books & Media', 24.99, 12.00, 20, 5),

            # Health & Beauty
            ('Face Moisturizer', 'FM-027', 'Health & Beauty', 18.99, 9.00, 45, 10),
            ('Natural Shampoo', 'NS-028', 'Health & Beauty', 12.99, 6.00, 60, 10),
        ]

        products = {}
        for name, sku, cat_name, price, cost, stock, threshold in products_data:
            if Product.objects.filter(sku=sku).exists():
                products[sku] = Product.objects.get(sku=sku)
                continue

            product = Product.objects.create(
                name=name,
                sku=sku,
                category=categories[cat_name],
                price=Decimal(str(price)),
                cost_price=Decimal(str(cost)),
                stock_quantity=stock,
                low_stock_threshold=threshold,
                is_active=True
            )
            products[sku] = product

            # Create initial stock movement
            if stock > 0:
                StockMovement.objects.create(
                    product=product,
                    movement_type='purchase',
                    quantity_change=stock,
                    quantity_before=0,
                    quantity_after=stock,
                    notes='Initial stock load',
                    created_by=admin
                )

        self.stdout.write(self.style.SUCCESS(f'  ✓ Created {len(products_data)} products'))

        # Create sample sales (last 30 days)
        product_list = list(Product.objects.filter(is_active=True, stock_quantity__gt=0))

        sales_created = 0
        for days_ago in range(30, 0, -1):
            # Create 1-5 sales per day
            num_sales = random.randint(1, 5)
            sale_date = timezone.now() - timedelta(days=days_ago)

            for _ in range(num_sales):
                if not product_list:
                    break

                customer_names = [
                    'John Smith', 'Emma Johnson', 'Michael Brown', 'Olivia Davis',
                    'William Wilson', 'Sophia Martinez', 'James Anderson', 'Walk-in Customer',
                    'Isabella Thomas', 'Oliver Jackson', 'Charlotte White', 'Elijah Harris',
                ]

                sale = Sale.objects.create(
                    customer_name=random.choice(customer_names),
                    created_by=random.choice([admin, demo_user]),
                    status='completed',
                    created_at=sale_date,
                )
                # Override auto_now_add
                Sale.objects.filter(pk=sale.pk).update(created_at=sale_date)

                # Add 1-4 items to each sale
                num_items = random.randint(1, 4)
                selected_products = random.sample(product_list, min(num_items, len(product_list)))

                for product in selected_products:
                    qty = random.randint(1, 3)
                    # Don't exceed available stock (leave some for display)
                    if product.stock_quantity > qty + 5:
                        SaleItem.objects.create(
                            sale=sale,
                            product=product,
                            quantity=qty,
                            unit_price=product.price,
                            discount=Decimal('0'),
                        )
                        # We don't reduce stock here to keep display values meaningful

                sales_created += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ Created {sales_created} sample sales'))
        self.stdout.write(self.style.SUCCESS('\n=== Sample Data Created Successfully! ==='))
        self.stdout.write(self.style.SUCCESS('\nLogin credentials:'))
        self.stdout.write(self.style.SUCCESS('  Admin:  username=admin    password=admin123'))
        self.stdout.write(self.style.SUCCESS('  Demo:   username=demo     password=demo123'))
        self.stdout.write(self.style.SUCCESS('\nRun: python manage.py runserver'))
        self.stdout.write(self.style.SUCCESS('Then visit: http://127.0.0.1:8000/'))
