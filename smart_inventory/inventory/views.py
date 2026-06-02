"""
Views for Smart Inventory Management System
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db.models import Sum, Count, Q, F
from django.db.models.functions import TruncDate, TruncMonth
from django.http import JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import timedelta, date
import json
from decimal import Decimal

from .models import Product, Category, Sale, SaleItem, StockMovement
from .forms import (UserRegistrationForm, ProductForm, CategoryForm,
                    SaleForm, SaleItemForm, StockUpdateForm, ProductSearchForm)


# ============================================================
# AUTHENTICATION VIEWS
# ============================================================

def register_view(request):
    """User registration"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome {user.first_name}! Your account has been created.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()

    return render(request, 'registration/register.html', {'form': form})


def login_view(request):
    """User login"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()

    return render(request, 'registration/login.html', {'form': form})


@login_required
def logout_view(request):
    """User logout"""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('login')


# ============================================================
# DASHBOARD VIEWS
# ============================================================

@login_required
def dashboard(request):
    """Main dashboard with analytics"""
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    seven_days_ago = today - timedelta(days=7)

    # --- Summary Cards ---
    total_products = Product.objects.filter(is_active=True).count()
    low_stock_count = Product.objects.filter(
        is_active=True,
        stock_quantity__lte=F('low_stock_threshold')
    ).count()
    out_of_stock = Product.objects.filter(is_active=True, stock_quantity=0).count()

    # Revenue calculations
    total_revenue = SaleItem.objects.filter(
        sale__status='completed'
    ).aggregate(
        total=Sum(F('unit_price') * F('quantity'))
    )['total'] or Decimal('0')

    monthly_revenue = SaleItem.objects.filter(
        sale__status='completed',
        sale__created_at__date__gte=thirty_days_ago
    ).aggregate(
        total=Sum(F('unit_price') * F('quantity'))
    )['total'] or Decimal('0')

    total_sales = Sale.objects.filter(status='completed').count()
    monthly_sales = Sale.objects.filter(
        status='completed',
        created_at__date__gte=thirty_days_ago
    ).count()

    # --- Recent Sales ---
    recent_sales = Sale.objects.filter(
        status='completed'
    ).prefetch_related('items__product').order_by('-created_at')[:5]

    # --- Low Stock Products ---
    low_stock_products = Product.objects.filter(
        is_active=True,
        stock_quantity__lte=F('low_stock_threshold')
    ).select_related('category').order_by('stock_quantity')[:8]

    # --- Chart Data: Last 7 days sales ---
    daily_sales_data = []
    daily_labels = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        daily_labels.append(day.strftime('%b %d'))
        day_revenue = SaleItem.objects.filter(
            sale__status='completed',
            sale__created_at__date=day
        ).aggregate(total=Sum(F('unit_price') * F('quantity')))['total'] or 0
        daily_sales_data.append(float(day_revenue))

    # --- Chart Data: Monthly revenue (last 6 months) ---
    monthly_labels = []
    monthly_data = []
    for i in range(5, -1, -1):
        # Calculate the month
        month_date = today.replace(day=1) - timedelta(days=i * 30)
        month_date = month_date.replace(day=1)
        monthly_labels.append(month_date.strftime('%b %Y'))
        month_revenue = SaleItem.objects.filter(
            sale__status='completed',
            sale__created_at__year=month_date.year,
            sale__created_at__month=month_date.month
        ).aggregate(total=Sum(F('unit_price') * F('quantity')))['total'] or 0
        monthly_data.append(float(month_revenue))

    # --- Chart Data: Category breakdown ---
    category_data = Category.objects.annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    ).filter(product_count__gt=0).values('name', 'product_count')

    category_labels = [c['name'] for c in category_data]
    category_counts = [c['product_count'] for c in category_data]

    # --- Top Products by Sales ---
    top_products = SaleItem.objects.filter(
        sale__status='completed',
        sale__created_at__date__gte=thirty_days_ago
    ).values(
        'product__name'
    ).annotate(
        total_qty=Sum('quantity'),
        total_rev=Sum(F('unit_price') * F('quantity'))
    ).order_by('-total_rev')[:5]

    context = {
        'total_products': total_products,
        'low_stock_count': low_stock_count,
        'out_of_stock': out_of_stock,
        'total_revenue': total_revenue,
        'monthly_revenue': monthly_revenue,
        'total_sales': total_sales,
        'monthly_sales': monthly_sales,
        'recent_sales': recent_sales,
        'low_stock_products': low_stock_products,
        'daily_labels': json.dumps(daily_labels),
        'daily_sales_data': json.dumps(daily_sales_data),
        'monthly_labels': json.dumps(monthly_labels),
        'monthly_data': json.dumps(monthly_data),
        'category_labels': json.dumps(category_labels),
        'category_counts': json.dumps(category_counts),
        'top_products': top_products,
    }
    return render(request, 'dashboard/dashboard.html', context)


# ============================================================
# PRODUCT VIEWS
# ============================================================

@login_required
def product_list(request):
    """List all products with search and filtering"""
    form = ProductSearchForm(request.GET)
    products = Product.objects.select_related('category').all()

    # Apply filters
    query = request.GET.get('query', '')
    category_id = request.GET.get('category', '')
    low_stock = request.GET.get('low_stock', '')

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(sku__icontains=query) |
            Q(description__icontains=query)
        )

    if category_id:
        products = products.filter(category_id=category_id)

    if low_stock:
        products = products.filter(stock_quantity__lte=F('low_stock_threshold'))

    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'products': page_obj,
        'form': form,
        'query': query,
        'total_count': products.count(),
    }
    return render(request, 'products/product_list.html', context)


@login_required
def product_detail(request, pk):
    """Product detail view with stock history"""
    product = get_object_or_404(Product, pk=pk)
    movements = StockMovement.objects.filter(product=product).order_by('-created_at')[:10]
    sale_items = SaleItem.objects.filter(product=product).select_related('sale').order_by('-sale__created_at')[:10]

    context = {
        'product': product,
        'movements': movements,
        'sale_items': sale_items,
    }
    return render(request, 'products/product_detail.html', context)


@login_required
def product_add(request):
    """Add new product"""
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            # Record initial stock movement
            if product.stock_quantity > 0:
                StockMovement.objects.create(
                    product=product,
                    movement_type='purchase',
                    quantity_change=product.stock_quantity,
                    quantity_before=0,
                    quantity_after=product.stock_quantity,
                    notes='Initial stock',
                    created_by=request.user
                )
            messages.success(request, f'Product "{product.name}" added successfully!')
            return redirect('product_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProductForm()

    return render(request, 'products/product_form.html', {'form': form, 'title': 'Add Product'})


@login_required
def product_edit(request, pk):
    """Edit existing product"""
    product = get_object_or_404(Product, pk=pk)
    old_stock = product.stock_quantity

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save()
            # Record stock change if quantity changed
            new_stock = product.stock_quantity
            if old_stock != new_stock:
                change = new_stock - old_stock
                StockMovement.objects.create(
                    product=product,
                    movement_type='adjustment',
                    quantity_change=change,
                    quantity_before=old_stock,
                    quantity_after=new_stock,
                    notes='Manual stock adjustment via product edit',
                    created_by=request.user
                )
            messages.success(request, f'Product "{product.name}" updated successfully!')
            return redirect('product_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProductForm(instance=product)

    return render(request, 'products/product_form.html', {
        'form': form,
        'product': product,
        'title': f'Edit: {product.name}'
    })


@login_required
def product_delete(request, pk):
    """Delete product with confirmation"""
    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f'Product "{name}" deleted successfully.')
        return redirect('product_list')

    return render(request, 'products/product_confirm_delete.html', {'product': product})


@login_required
def category_list(request):
    """List all categories"""
    categories = Category.objects.annotate(product_count=Count('products')).order_by('name')
    return render(request, 'products/category_list.html', {'categories': categories})


@login_required
def category_add(request):
    """Add new category"""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" added successfully!')
            return redirect('category_list')
    else:
        form = CategoryForm()
    return render(request, 'products/category_form.html', {'form': form, 'title': 'Add Category'})


@login_required
def category_edit(request, pk):
    """Edit category"""
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" updated!')
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'products/category_form.html', {
        'form': form,
        'category': category,
        'title': f'Edit: {category.name}'
    })


@login_required
def category_delete(request, pk):
    """Delete category"""
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        name = category.name
        category.delete()
        messages.success(request, f'Category "{name}" deleted.')
        return redirect('category_list')
    return render(request, 'products/category_confirm_delete.html', {'category': category})


# ============================================================
# SALES VIEWS
# ============================================================

@login_required
def sale_list(request):
    """List all sales with pagination"""
    sales = Sale.objects.prefetch_related('items__product').order_by('-created_at')

    # Filter by date
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        sales = sales.filter(created_at__date__gte=start_date)
    if end_date:
        sales = sales.filter(created_at__date__lte=end_date)

    # Pagination
    paginator = Paginator(sales, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'sales': page_obj,
        'start_date': start_date or '',
        'end_date': end_date or '',
    }
    return render(request, 'sales/sale_list.html', context)


@login_required
def sale_detail(request, pk):
    """Sale detail / receipt view"""
    sale = get_object_or_404(Sale, pk=pk)
    items = sale.items.select_related('product').all()
    context = {
        'sale': sale,
        'items': items,
    }
    return render(request, 'sales/sale_detail.html', context)


@login_required
def sale_create(request):
    """Create a new sale with multiple items"""
    products = Product.objects.filter(is_active=True, stock_quantity__gt=0).select_related('category')

    if request.method == 'POST':
        sale_form = SaleForm(request.POST)

        if sale_form.is_valid():
            # Parse items from POST data
            product_ids = request.POST.getlist('product_id[]')
            quantities = request.POST.getlist('quantity[]')
            unit_prices = request.POST.getlist('unit_price[]')
            discounts = request.POST.getlist('discount[]')

            if not product_ids:
                messages.error(request, 'Please add at least one product to the sale.')
                return render(request, 'sales/sale_create.html', {
                    'sale_form': sale_form,
                    'products': products
                })

            # Create the sale
            sale = sale_form.save(commit=False)
            sale.created_by = request.user
            sale.status = 'completed'
            sale.save()

            # Process each item
            errors = []
            for i, product_id in enumerate(product_ids):
                try:
                    product = Product.objects.get(pk=product_id)
                    qty = int(quantities[i]) if i < len(quantities) else 1
                    unit_price = Decimal(unit_prices[i]) if i < len(unit_prices) and unit_prices[i] else product.price
                    discount = Decimal(discounts[i]) if i < len(discounts) and discounts[i] else Decimal('0')

                    # Check stock
                    if product.stock_quantity < qty:
                        errors.append(f'Insufficient stock for {product.name}. Available: {product.stock_quantity}')
                        continue

                    # Create sale item
                    SaleItem.objects.create(
                        sale=sale,
                        product=product,
                        quantity=qty,
                        unit_price=unit_price,
                        discount=discount
                    )

                    # Update stock
                    old_stock = product.stock_quantity
                    product.stock_quantity -= qty
                    product.save()

                    # Record stock movement
                    StockMovement.objects.create(
                        product=product,
                        movement_type='sale',
                        quantity_change=-qty,
                        quantity_before=old_stock,
                        quantity_after=product.stock_quantity,
                        reference=sale.sale_number,
                        notes=f'Sold in {sale.sale_number}',
                        created_by=request.user
                    )

                except Product.DoesNotExist:
                    errors.append(f'Product with ID {product_id} not found.')

            if errors:
                for error in errors:
                    messages.warning(request, error)

            messages.success(request, f'Sale {sale.sale_number} created successfully!')
            return redirect('sale_detail', pk=sale.pk)
        else:
            messages.error(request, 'Please correct the form errors.')

    else:
        sale_form = SaleForm()

    context = {
        'sale_form': sale_form,
        'products': products,
    }
    return render(request, 'sales/sale_create.html', context)


@login_required
def sale_cancel(request, pk):
    """Cancel a sale and restore stock"""
    sale = get_object_or_404(Sale, pk=pk)

    if request.method == 'POST':
        if sale.status == 'completed':
            # Restore stock for each item
            for item in sale.items.select_related('product').all():
                old_stock = item.product.stock_quantity
                item.product.stock_quantity += item.quantity
                item.product.save()

                StockMovement.objects.create(
                    product=item.product,
                    movement_type='return',
                    quantity_change=item.quantity,
                    quantity_before=old_stock,
                    quantity_after=item.product.stock_quantity,
                    reference=sale.sale_number,
                    notes=f'Sale {sale.sale_number} cancelled',
                    created_by=request.user
                )

            sale.status = 'cancelled'
            sale.save()
            messages.success(request, f'Sale {sale.sale_number} has been cancelled and stock restored.')
        else:
            messages.warning(request, 'This sale cannot be cancelled.')

        return redirect('sale_detail', pk=sale.pk)

    return render(request, 'sales/sale_cancel_confirm.html', {'sale': sale})


# ============================================================
# INVENTORY MANAGEMENT VIEWS
# ============================================================

@login_required
def inventory_view(request):
    """Inventory overview"""
    products = Product.objects.select_related('category').filter(is_active=True)

    # Stats
    total_stock_value = sum(p.stock_value for p in products)
    low_stock_items = products.filter(stock_quantity__lte=F('low_stock_threshold'))
    out_of_stock_items = products.filter(stock_quantity=0)

    # Recent movements
    recent_movements = StockMovement.objects.select_related(
        'product', 'created_by'
    ).order_by('-created_at')[:20]

    context = {
        'products': products,
        'total_stock_value': total_stock_value,
        'low_stock_items': low_stock_items,
        'out_of_stock_items': out_of_stock_items,
        'recent_movements': recent_movements,
    }
    return render(request, 'inventory/inventory.html', context)


@login_required
def stock_update(request):
    """Manually update stock levels"""
    if request.method == 'POST':
        form = StockUpdateForm(request.POST)
        if form.is_valid():
            product = form.cleaned_data['product']
            quantity_change = form.cleaned_data['quantity_change']
            notes = form.cleaned_data.get('notes', '')

            old_stock = product.stock_quantity
            new_stock = old_stock + quantity_change

            if new_stock < 0:
                messages.error(request, f'Cannot reduce stock below 0. Current stock: {old_stock}')
            else:
                product.stock_quantity = new_stock
                product.save()

                StockMovement.objects.create(
                    product=product,
                    movement_type='adjustment',
                    quantity_change=quantity_change,
                    quantity_before=old_stock,
                    quantity_after=new_stock,
                    notes=notes or 'Manual stock adjustment',
                    created_by=request.user
                )
                messages.success(
                    request,
                    f'Stock updated for {product.name}: {old_stock} → {new_stock} ({quantity_change:+d})'
                )
                return redirect('inventory')
    else:
        form = StockUpdateForm()

    return render(request, 'inventory/stock_update.html', {'form': form})


# ============================================================
# REPORTS VIEWS
# ============================================================

@login_required
def reports_view(request):
    """Revenue reports overview"""
    today = timezone.now().date()

    # Daily report (today)
    today_sales = Sale.objects.filter(status='completed', created_at__date=today)
    today_revenue = SaleItem.objects.filter(
        sale__in=today_sales
    ).aggregate(total=Sum(F('unit_price') * F('quantity')))['total'] or Decimal('0')

    # Weekly report (last 7 days)
    week_start = today - timedelta(days=7)
    week_sales = Sale.objects.filter(status='completed', created_at__date__gte=week_start)
    week_revenue = SaleItem.objects.filter(
        sale__in=week_sales
    ).aggregate(total=Sum(F('unit_price') * F('quantity')))['total'] or Decimal('0')

    # Monthly report (current month)
    month_start = today.replace(day=1)
    month_sales = Sale.objects.filter(status='completed', created_at__date__gte=month_start)
    month_revenue = SaleItem.objects.filter(
        sale__in=month_sales
    ).aggregate(total=Sum(F('unit_price') * F('quantity')))['total'] or Decimal('0')

    # Total all-time
    total_revenue = SaleItem.objects.filter(
        sale__status='completed'
    ).aggregate(total=Sum(F('unit_price') * F('quantity')))['total'] or Decimal('0')

    # Daily breakdown for current month
    daily_breakdown = []
    current_day = month_start
    while current_day <= today:
        day_rev = SaleItem.objects.filter(
            sale__status='completed',
            sale__created_at__date=current_day
        ).aggregate(total=Sum(F('unit_price') * F('quantity')))['total'] or 0
        day_count = Sale.objects.filter(
            status='completed',
            created_at__date=current_day
        ).count()
        daily_breakdown.append({
            'date': current_day,
            'revenue': float(day_rev),
            'sales_count': day_count,
        })
        current_day += timedelta(days=1)

    # Top selling products this month
    top_products_month = SaleItem.objects.filter(
        sale__status='completed',
        sale__created_at__date__gte=month_start
    ).values('product__name', 'product__sku').annotate(
        total_qty=Sum('quantity'),
        total_rev=Sum(F('unit_price') * F('quantity'))
    ).order_by('-total_rev')[:10]

    # Monthly summary (last 12 months)
    monthly_summary = []
    for i in range(11, -1, -1):
        m_date = today.replace(day=1) - timedelta(days=i * 30)
        m_date = m_date.replace(day=1)
        m_rev = SaleItem.objects.filter(
            sale__status='completed',
            sale__created_at__year=m_date.year,
            sale__created_at__month=m_date.month
        ).aggregate(total=Sum(F('unit_price') * F('quantity')))['total'] or 0
        m_count = Sale.objects.filter(
            status='completed',
            created_at__year=m_date.year,
            created_at__month=m_date.month
        ).count()
        monthly_summary.append({
            'month': m_date.strftime('%B %Y'),
            'revenue': float(m_rev),
            'sales_count': m_count,
        })

    context = {
        'today': today,
        'today_revenue': today_revenue,
        'today_sales_count': today_sales.count(),
        'week_revenue': week_revenue,
        'week_sales_count': week_sales.count(),
        'month_revenue': month_revenue,
        'month_sales_count': month_sales.count(),
        'total_revenue': total_revenue,
        'total_sales': Sale.objects.filter(status='completed').count(),
        'daily_breakdown': daily_breakdown,
        'top_products_month': top_products_month,
        'monthly_summary': monthly_summary,
    }
    return render(request, 'reports/reports.html', context)


# ============================================================
# API / AJAX VIEWS
# ============================================================

@login_required
def get_product_price(request):
    """AJAX: Get product price and stock info"""
    product_id = request.GET.get('product_id')
    if product_id:
        try:
            product = Product.objects.get(pk=product_id)
            return JsonResponse({
                'success': True,
                'price': float(product.price),
                'stock': product.stock_quantity,
                'name': product.name,
                'sku': product.sku,
            })
        except Product.DoesNotExist:
            pass
    return JsonResponse({'success': False})
