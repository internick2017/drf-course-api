from rest_framework import serializers
from .models import User, Product, Order, OrderItem


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model with validation"""

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'stock', 'image', 'in_stock']
        read_only_fields = ['id', 'in_stock']

    def validate_price(self, value):
        """Validate that price is greater than 0"""
        if value <= 0:
            raise serializers.ValidationError(
                "Price must be greater than 0."
            )
        return value

    def validate_stock(self, value):
        """Validate that stock is not negative"""
        if value < 0:
            raise serializers.ValidationError(
                "Stock cannot be negative."
            )
        return value


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for OrderItem model with product details"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        source='product.price',
        read_only=True
    )
    item_subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'product_price', 'quantity', 'item_subtotal']
        read_only_fields = ['id', 'product_name', 'product_price', 'item_subtotal']

    def validate_quantity(self, value):
        """Validate that quantity is greater than 0"""
        if value <= 0:
            raise serializers.ValidationError(
                "Quantity must be greater than 0."
            )
        return value


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for Order model with items and total calculation"""
    items = OrderItemSerializer(many=True, read_only=True, source='order_items')
    total_price = serializers.SerializerMethodField(method_name='calculate_total')
    user_username = serializers.CharField(source='user.username', read_only=True)

    def calculate_total(self, obj):
        """Calculate total price of the order"""
        order_items = obj.order_items.all()
        return sum(order_item.item_subtotal for order_item in order_items)

    class Meta:
        model = Order
        fields = ['order_id', 'user', 'user_username', 'created_at', 'status', 'items', 'total_price']
        read_only_fields = ['order_id', 'created_at', 'items', 'user_username', 'total_price']


class ProductInfoSerializer(serializers.Serializer):
    """Serializer for product information and statistics"""
    products = ProductSerializer(many=True)
    count = serializers.IntegerField()
    max_price = serializers.FloatField()
    min_price = serializers.FloatField()
    average_price = serializers.FloatField()
    in_stock_count = serializers.IntegerField()
    out_of_stock_count = serializers.IntegerField()