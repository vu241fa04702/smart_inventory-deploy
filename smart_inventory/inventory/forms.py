"""
Forms for Smart Inventory Management System
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Product, Category, Sale, SaleItem


class UserRegistrationForm(UserCreationForm):
    """Extended user registration form"""
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter email address'
    }))
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'First name'
    }))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Last name'
    }))

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose a username'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to password fields
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Create password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm password'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user


class CategoryForm(forms.ModelForm):
    """Form for creating and editing product categories"""

    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Category name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description (optional)'}),
        }


class ProductForm(forms.ModelForm):
    """Form for creating and editing products"""

    class Meta:
        model = Product
        fields = ['name', 'sku', 'category', 'description', 'price', 'cost_price',
                  'stock_quantity', 'low_stock_threshold', 'image', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Product name'}),
            'sku': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. PROD-001'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'cost_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'low_stock_threshold': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SaleForm(forms.ModelForm):
    """Form for creating sales"""

    class Meta:
        model = Sale
        fields = ['customer_name', 'customer_email', 'customer_phone', 'notes']
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Customer name'}),
            'customer_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'customer@email.com'}),
            'customer_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1 234 567 8900'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Additional notes...'}),
        }


class SaleItemForm(forms.ModelForm):
    """Form for adding items to a sale"""
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(is_active=True, stock_quantity__gt=0),
        widget=forms.Select(attrs={'class': 'form-select product-select'})
    )

    class Meta:
        model = SaleItem
        fields = ['product', 'quantity', 'unit_price', 'discount']
        widgets = {
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'value': '1'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100', 'value': '0'}),
        }


class StockUpdateForm(forms.Form):
    """Form for manually updating stock levels"""
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    quantity_change = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter positive or negative number'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Reason for adjustment'})
    )


class ProductSearchForm(forms.Form):
    """Form for searching and filtering products"""
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search products...',
            'id': 'search-input'
        })
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label='All Categories',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    low_stock = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
