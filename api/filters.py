import django_filters  # type: ignore
from django.db.models import Q
from .models import User, Product, Order, OrderItem


class UserFilter(django_filters.FilterSet):
    """
    Advanced filtering for User model
    """
    search = django_filters.CharFilter(method='search_filter', label='Search in username, first_name, last_name, email')
    username = django_filters.CharFilter(lookup_expr='icontains', label='Username contains')
    email = django_filters.CharFilter(lookup_expr='icontains', label='Email contains')
    email_domain = django_filters.CharFilter(method='email_domain_filter', label='Email domain')
    first_name = django_filters.CharFilter(lookup_expr='icontains', label='First name contains')
    last_name = django_filters.CharFilter(lookup_expr='icontains', label='Last name contains')
    is_active = django_filters.BooleanFilter(label='Active status')
    is_staff = django_filters.BooleanFilter(label='Staff status')
    date_joined_after = django_filters.DateFilter(field_name='date_joined', lookup_expr='gte', label='Joined after date')
    date_joined_before = django_filters.DateFilter(field_name='date_joined', lookup_expr='lte', label='Joined before date')
    has_orders = django_filters.BooleanFilter(method='has_orders_filter', label='Has orders')

    class Meta:
        model = User
        fields = {
            'username': ['exact', 'icontains'],
            'email': ['exact', 'icontains'],
            'first_name': ['exact', 'icontains'],
            'last_name': ['exact', 'icontains'],
            'is_active': ['exact'],
            'is_staff': ['exact'],
            'date_joined': ['exact', 'gte', 'lte'],
        }

    def search_filter(self, queryset, name, value):
        """Search across multiple user fields"""
        return queryset.filter(
            Q(username__icontains=value) |
            Q(first_name__icontains=value) |
            Q(last_name__icontains=value) |
            Q(email__icontains=value)
        )

    def email_domain_filter(self, queryset, name, value):
        """Filter by email domain"""
        return queryset.filter(email__endswith=f'@{value}')

    def has_orders_filter(self, queryset, name, value):
        """Filter users who have/haven't placed orders"""
        if value:
            return queryset.filter(order__isnull=False).distinct()
        else:
            return queryset.filter(order__isnull=True)


class ProductFilter(django_filters.FilterSet):
    """
    Advanced filtering for Product model
    """
    search = django_filters.CharFilter(method='search_filter', label='Search in name and description')
    name = django_filters.CharFilter(lookup_expr='icontains', label='Product name contains')
    description = django_filters.CharFilter(lookup_expr='icontains', label='Description contains')
    in_stock = django_filters.BooleanFilter(method='in_stock_filter', label='In stock')
    out_of_stock = django_filters.BooleanFilter(method='out_of_stock_filter', label='Out of stock')
    price_min = django_filters.NumberFilter(field_name='price', lookup_expr='gte', label='Minimum price')
    price_max = django_filters.NumberFilter(field_name='price', lookup_expr='lte', label='Maximum price')
    stock_min = django_filters.NumberFilter(field_name='stock', lookup_expr='gte', label='Minimum stock')
    stock_max = django_filters.NumberFilter(field_name='stock', lookup_expr='lte', label='Maximum stock')
    has_orders = django_filters.BooleanFilter(method='has_orders_filter', label='Has been ordered')

    class Meta:
        model = Product
        fields = {
            'name': ['exact', 'icontains'],
            'description': ['exact', 'icontains'],
            'price': ['exact', 'gte', 'lte'],
            'stock': ['exact', 'gte', 'lte'],
        }

    def search_filter(self, queryset, name, value):
        """Search across product name and description"""
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value)
        )

    def in_stock_filter(self, queryset, name, value):
        """Filter products in stock"""
        if value:
            return queryset.filter(stock__gt=0)
        return queryset

    def out_of_stock_filter(self, queryset, name, value):
        """Filter products out of stock"""
        if value:
            return queryset.filter(stock=0)
        return queryset

    def has_orders_filter(self, queryset, name, value):
        """Filter products that have/haven't been ordered"""
        if value:
            return queryset.filter(orderitem__isnull=False).distinct()
        else:
            return queryset.filter(orderitem__isnull=True)


class OrderFilter(django_filters.FilterSet):
    """
    Advanced filtering for Order model
    """
    order_id = django_filters.CharFilter(lookup_expr='icontains', label='Order ID contains')
    user_username = django_filters.CharFilter(field_name='user__username', lookup_expr='icontains', label='User username')
    user_email = django_filters.CharFilter(field_name='user__email', lookup_expr='icontains', label='User email')
    status = django_filters.ChoiceFilter(choices=Order.StatusChoices.choices, label='Order status')
    has_items = django_filters.BooleanFilter(method='has_items_filter', label='Has order items')
    created_after = django_filters.DateFilter(field_name='created_at', lookup_expr='gte', label='Created after date')
    created_before = django_filters.DateFilter(field_name='created_at', lookup_expr='lte', label='Created before date')

    class Meta:
        model = Order
        fields = {
            'order_id': ['exact', 'icontains'],
            'status': ['exact'],
            'created_at': ['exact', 'gte', 'lte'],
        }

    def has_items_filter(self, queryset, name, value):
        """Filter orders that have/haven't items"""
        if value:
            return queryset.filter(items__isnull=False).distinct()
        else:
            return queryset.filter(items__isnull=True)




class OrderItemFilter(django_filters.FilterSet):
    """
    Advanced filtering for OrderItem model
    """
    order_id = django_filters.CharFilter(field_name='order__order_id', lookup_expr='icontains', label='Order ID')
    product_name = django_filters.CharFilter(field_name='product__name', lookup_expr='icontains', label='Product name')
    product_id = django_filters.NumberFilter(field_name='product__id', label='Product ID')
    user_username = django_filters.CharFilter(field_name='order__user__username', lookup_expr='icontains', label='User username')
    quantity_min = django_filters.NumberFilter(field_name='quantity', lookup_expr='gte', label='Minimum quantity')
    quantity_max = django_filters.NumberFilter(field_name='quantity', lookup_expr='lte', label='Maximum quantity')
    created_after = django_filters.DateFilter(field_name='order__created_at', lookup_expr='gte', label='Order created after')
    created_before = django_filters.DateFilter(field_name='order__created_at', lookup_expr='lte', label='Order created before')

    class Meta:
        model = OrderItem
        fields = {
            'quantity': ['exact', 'gte', 'lte'],
            'product__id': ['exact'],
            'order__order_id': ['exact', 'icontains'],
        }


