from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Product, Order, OrderItem


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Admin configuration for custom User model"""
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-date_joined']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin configuration for Product model"""
    list_display = ['name', 'price', 'stock', 'in_stock']
    list_filter = ['stock']
    search_fields = ['name', 'description']
    ordering = ['name']


class OrderItemInline(admin.TabularInline):
    """Inline admin for OrderItem"""
    model = OrderItem
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin configuration for Order model"""
    list_display = ['order_id', 'user', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order_id', 'user__username']
    ordering = ['-created_at']
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Admin configuration for OrderItem model"""
    list_display = ['order', 'product', 'quantity', 'item_subtotal']
    list_filter = ['order__status']
    search_fields = ['order__order_id', 'product__name']
