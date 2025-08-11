from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from django.db.models import Max, Avg, Q, Sum
from django.utils.dateparse import parse_date
import time
import random
from silk.profiling.profiler import silk_profile
from .models import User, Product, Order, OrderItem
from .serializers import UserSerializer, ProductSerializer, OrderSerializer, OrderItemSerializer, ProductInfoSerializer
from .permissions import (
    IsOrderOwner, IsOrderItemOwner,
    IsAdminOrReadOnly, IsAuthenticatedOrReadOnlyForProducts
)


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for User model with dynamic filtering"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminOrReadOnly]  # Only admins can manage users

    def get_queryset(self):
        """
        Dynamic filtering for User ViewSet
        """
        queryset = User.objects.all()
        queryset = self._apply_search_filter(queryset)
        queryset = self._apply_email_domain_filter(queryset)
        queryset = self._apply_active_status_filter(queryset)
        queryset = self._apply_date_range_filters(queryset)
        queryset = self._apply_ordering(queryset)
        return queryset

    def _apply_search_filter(self, queryset):
        """Apply search filter to queryset"""
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search)
            )
        return queryset

    def _apply_email_domain_filter(self, queryset):
        """Apply email domain filter to queryset"""
        email_domain = self.request.query_params.get('email_domain', None)
        if email_domain:
            queryset = queryset.filter(email__endswith=f'@{email_domain}')
        return queryset

    def _apply_active_status_filter(self, queryset):
        """Apply active status filter to queryset"""
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            if is_active.lower() == 'true':
                queryset = queryset.filter(is_active=True)
            elif is_active.lower() == 'false':
                queryset = queryset.filter(is_active=False)
        return queryset

    def _apply_date_range_filters(self, queryset):
        """Apply date range filters to queryset"""
        date_joined_after = self.request.query_params.get('date_joined_after', None)
        date_joined_before = self.request.query_params.get('date_joined_before', None)

        if date_joined_after:
            try:
                date_after = parse_date(date_joined_after)
                if date_after:
                    queryset = queryset.filter(date_joined__gte=date_after)
            except ValueError:
                pass

        if date_joined_before:
            try:
                date_before = parse_date(date_joined_before)
                if date_before:
                    queryset = queryset.filter(date_joined__lte=date_before)
            except ValueError:
                pass

        return queryset

    def _apply_ordering(self, queryset):
        """Apply ordering to queryset"""
        ordering = self.request.query_params.get('ordering', None)
        if ordering:
            allowed_fields = ['username', 'email', 'first_name', 'last_name', 'date_joined',
                            '-username', '-email', '-first_name', '-last_name', '-date_joined']
            if ordering in allowed_fields:
                queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('username')
        return queryset


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet for Product model with dynamic filtering"""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnlyForProducts]  # Read for everyone, write for authenticated

    def get_queryset(self):
        """
        Dynamic filtering for Product ViewSet
        """
        queryset = Product.objects.all()
        queryset = self._apply_search_filter(queryset)
        queryset = self._apply_stock_availability_filter(queryset)
        queryset = self._apply_price_range_filters(queryset)
        queryset = self._apply_stock_range_filters(queryset)
        queryset = self._apply_ordering(queryset)
        return queryset

    def _apply_search_filter(self, queryset):
        """Apply search filter to queryset"""
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        return queryset

    def _apply_stock_availability_filter(self, queryset):
        """Apply stock availability filter to queryset"""
        in_stock = self.request.query_params.get('in_stock', None)
        if in_stock is not None:
            if in_stock.lower() == 'true':
                queryset = queryset.filter(stock__gt=0)
            elif in_stock.lower() == 'false':
                queryset = queryset.filter(stock=0)
        return queryset

    def _apply_price_range_filters(self, queryset):
        """Apply price range filters to queryset"""
        min_price = self.request.query_params.get('min_price', None)
        max_price = self.request.query_params.get('max_price', None)

        if min_price is not None:
            try:
                queryset = queryset.filter(price__gte=float(min_price))
            except ValueError:
                pass

        if max_price is not None:
            try:
                queryset = queryset.filter(price__lte=float(max_price))
            except ValueError:
                pass
        return queryset

    def _apply_stock_range_filters(self, queryset):
        """Apply stock range filters to queryset"""
        min_stock = self.request.query_params.get('min_stock', None)
        max_stock = self.request.query_params.get('max_stock', None)

        if min_stock is not None:
            try:
                queryset = queryset.filter(stock__gte=int(min_stock))
            except ValueError:
                pass

        if max_stock is not None:
            try:
                queryset = queryset.filter(stock__lte=int(max_stock))
            except ValueError:
                pass
        return queryset

    def _apply_ordering(self, queryset):
        """Apply ordering to queryset"""
        ordering = self.request.query_params.get('ordering', None)
        if ordering:
            allowed_fields = ['name', 'price', 'stock', 'id', '-name', '-price', '-stock', '-id']
            if ordering in allowed_fields:
                queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('name')
        return queryset

    @action(detail=True, methods=['get'])
    def in_stock(self, request, pk=None):
        """Check if a product is in stock"""
        product = self.get_object()
        return Response({'in_stock': product.in_stock})


class OrderViewSet(viewsets.ModelViewSet):
    """ViewSet for Order model with dynamic filtering"""
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsOrderOwner]  # Users can only access their own orders

    def get_queryset(self):
        """
        Dynamic filtering for Order ViewSet with user-specific access
        """
        # Use prefetch_related for optimized queries
        queryset = Order.objects.prefetch_related('items__product').filter(user=self.request.user)
        queryset = self._apply_status_filter(queryset)
        queryset = self._apply_date_range_filters(queryset)
        queryset = self._apply_items_filter(queryset)
        queryset = self._apply_ordering(queryset)
        return queryset

    def _apply_status_filter(self, queryset):
        """Apply status filter to queryset"""
        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def _apply_date_range_filters(self, queryset):
        """Apply date range filters to queryset"""
        created_after = self.request.query_params.get('created_after', None)
        created_before = self.request.query_params.get('created_before', None)

        if created_after:
            try:
                date_after = parse_date(created_after)
                if date_after:
                    queryset = queryset.filter(created_at__gte=date_after)
            except ValueError:
                pass

        if created_before:
            try:
                date_before = parse_date(created_before)
                if date_before:
                    queryset = queryset.filter(created_at__lte=date_before)
            except ValueError:
                pass
        return queryset

    def _apply_items_filter(self, queryset):
        """Apply items filter to queryset"""
        has_items = self.request.query_params.get('has_items', None)
        if has_items is not None:
            if has_items.lower() == 'true':
                queryset = queryset.filter(items__isnull=False).distinct()
            elif has_items.lower() == 'false':
                queryset = queryset.filter(items__isnull=True)
        return queryset

    def _apply_ordering(self, queryset):
        """Apply ordering to queryset"""
        ordering = self.request.query_params.get('ordering', None)
        if ordering:
            allowed_fields = ['created_at', 'status', 'order_id', '-created_at', '-status', '-order_id']
            if ordering in allowed_fields:
                queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('-created_at')
        return queryset

    def perform_create(self, serializer):
        """Set the user to the current user when creating an order"""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get order statistics for the current user"""
        user_orders = self.get_queryset()

        stats = {
            'total_orders': user_orders.count(),
            'pending_orders': user_orders.filter(status='Pending').count(),
            'confirmed_orders': user_orders.filter(status='Confirmed').count(),
            'cancelled_orders': user_orders.filter(status='Cancelled').count(),
            'orders_with_items': user_orders.filter(items__isnull=False).distinct().count(),
            'orders_without_items': user_orders.filter(items__isnull=True).count(),
        }

        return Response(stats)


class OrderItemViewSet(viewsets.ModelViewSet):
    """ViewSet for OrderItem model with dynamic filtering"""
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    permission_classes = [IsOrderItemOwner]  # Users can only access their own order items

    def get_queryset(self):
        """
        Dynamic filtering for OrderItem ViewSet
        """
        queryset = OrderItem.objects.select_related('order', 'product')
        queryset = self._apply_order_filter(queryset)
        queryset = self._apply_product_filter(queryset)
        queryset = self._apply_quantity_range_filters(queryset)
        queryset = self._apply_subtotal_range_filters(queryset)
        queryset = self._apply_ordering(queryset)
        return queryset

    def _apply_order_filter(self, queryset):
        """Apply order filter to queryset"""
        order_id = self.request.query_params.get('order_id', None)
        if order_id:
            queryset = queryset.filter(order__order_id=order_id)
        return queryset

    def _apply_product_filter(self, queryset):
        """Apply product filter to queryset"""
        product_id = self.request.query_params.get('product_id', None)
        if product_id:
            queryset = queryset.filter(product__id=product_id)
        return queryset

    def _apply_quantity_range_filters(self, queryset):
        """Apply quantity range filters to queryset"""
        min_quantity = self.request.query_params.get('min_quantity', None)
        max_quantity = self.request.query_params.get('max_quantity', None)

        if min_quantity is not None:
            try:
                queryset = queryset.filter(quantity__gte=int(min_quantity))
            except ValueError:
                pass

        if max_quantity is not None:
            try:
                queryset = queryset.filter(quantity__lte=int(max_quantity))
            except ValueError:
                pass
        return queryset

    def _apply_subtotal_range_filters(self, queryset):
        """Apply subtotal range filters to queryset"""
        min_subtotal = self.request.query_params.get('min_subtotal', None)
        max_subtotal = self.request.query_params.get('max_subtotal', None)

        if min_subtotal is not None:
            try:
                queryset = queryset.filter(product__price__gte=float(min_subtotal))
            except ValueError:
                pass

        if max_subtotal is not None:
            try:
                queryset = queryset.filter(product__price__lte=float(max_subtotal))
            except ValueError:
                pass
        return queryset

    def _apply_ordering(self, queryset):
        """Apply ordering to queryset"""
        ordering = self.request.query_params.get('ordering', None)
        if ordering:
            allowed_fields = ['quantity', 'product__name', 'order__created_at',
                            '-quantity', '-product__name', '-order__created_at']
            if ordering in allowed_fields:
                queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('-order__created_at')
        return queryset


class ProfilingExampleView(APIView):
    """Example view demonstrating django-silk profiling techniques"""
    permission_classes = [IsAuthenticated]

    @silk_profile(name='expensive_calculation')
    def expensive_calculation(self, iterations):
        """Simulate an expensive calculation that will be profiled"""
        result = 0
        for i in range(iterations):
            result += i * random.random()
        return result

    @silk_profile(name='database_heavy_operation')
    def database_heavy_operation(self):
        """Simulate a database-heavy operation"""
        # This will be automatically profiled by Silk
        users = User.objects.all()
        products = Product.objects.all()
        orders = Order.objects.all()

        # Simulate some complex queries
        user_count = users.count()
        product_count = products.count()
        order_count = orders.count()

        return {
            'user_count': user_count,
            'product_count': product_count,
            'order_count': order_count
        }

    def get(self, request):
        """Main endpoint demonstrating different profiling techniques"""
        start_time = time.time()

        # Example 1: Manual profiling with silk_profile decorator
        expensive_result = self.expensive_calculation(10000)

        # Example 2: Database operation profiling (automatic)
        db_stats = self.database_heavy_operation()

        # Example 3: Manual timing for comparison
        manual_start = time.time()
        time.sleep(0.1)  # Simulate some work
        manual_time = time.time() - manual_start

        total_time = time.time() - start_time

        return Response({
            'message': 'Profiling example completed',
            'expensive_calculation_result': expensive_result,
            'database_stats': db_stats,
            'manual_timing': manual_time,
            'total_request_time': total_time,
            'profiling_info': {
                'silk_enabled': True,
                'profiling_url': '/silk/',
                'note': 'Check /silk/ for detailed profiling data'
            }
        })


class PerformanceTestView(APIView):
    """View for testing different performance scenarios"""
    permission_classes = [IsAuthenticated]

    @silk_profile(name='n_plus_one_query_test')
    def n_plus_one_query_test(self):
        """Demonstrate N+1 query problem for profiling"""
        orders = Order.objects.all()[:10]  # Get first 10 orders

        # This will cause N+1 queries - each order.user will hit the database
        order_data = []
        for order in orders:
            order_data.append({
                'order_id': order.id,
                'user_email': order.user.email,  # This causes additional query
                'total_amount': order.total_amount
            })

        return order_data

    @silk_profile(name='optimized_query_test')
    def optimized_query_test(self):
        """Demonstrate optimized query with select_related"""
        # This uses select_related to avoid N+1 queries
        orders = Order.objects.select_related('user').all()[:10]

        order_data = []
        for order in orders:
            order_data.append({
                'order_id': order.id,
                'user_email': order.user.email,  # No additional query needed
                'total_amount': order.total_amount
            })

        return order_data

    def get(self, request):
        """Compare N+1 vs optimized queries"""
        test_type = request.GET.get('test', 'both')

        if test_type == 'n_plus_one':
            result = self.n_plus_one_query_test()
            return Response({
                'test_type': 'N+1 Query Test',
                'data': result,
                'note': 'Check Silk for query count comparison'
            })
        elif test_type == 'optimized':
            result = self.optimized_query_test()
            return Response({
                'test_type': 'Optimized Query Test',
                'data': result,
                'note': 'Check Silk for query count comparison'
            })
        else:
            # Run both for comparison
            n_plus_one_result = self.n_plus_one_query_test()
            optimized_result = self.optimized_query_test()

            return Response({
                'n_plus_one_test': {
                    'data': n_plus_one_result,
                    'note': 'This should show more database queries in Silk'
                },
                'optimized_test': {
                    'data': optimized_result,
                    'note': 'This should show fewer database queries in Silk'
                },
                'comparison_note': 'Compare the number of SQL queries in Silk dashboard'
            })


# Generic Views Examples - ListAPIView & RetrieveAPIView

class ProductListAPIView(ListAPIView):
    """
    Generic view for listing all products with advanced dynamic filtering

    Available filters:
    - search: Search in name and description
    - in_stock: true/false for stock availability
    - min_price, max_price: Price range filtering
    - category: Filter by category (if you add this field)
    - ordering: Sort by any field (name, price, stock, created_at)
    - limit: Limit number of results
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnlyForProducts]  # Read for everyone, write for authenticated

    def get_queryset(self):
        """
        Advanced dynamic filtering for products
        """
        queryset = Product.objects.all()
        queryset = self._apply_search_filter(queryset)
        queryset = self._apply_stock_availability_filter(queryset)
        queryset = self._apply_price_range_filters(queryset)
        queryset = self._apply_stock_range_filters(queryset)
        queryset = self._apply_ordering(queryset)
        queryset = self._apply_limit(queryset)
        return queryset

    def _apply_search_filter(self, queryset):
        """Apply search filter to queryset"""
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        return queryset

    def _apply_stock_availability_filter(self, queryset):
        """Apply stock availability filter to queryset"""
        in_stock = self.request.query_params.get('in_stock', None)
        if in_stock is not None:
            if in_stock.lower() == 'true':
                queryset = queryset.filter(stock__gt=0)
            elif in_stock.lower() == 'false':
                queryset = queryset.filter(stock=0)
        return queryset

    def _apply_price_range_filters(self, queryset):
        """Apply price range filters to queryset"""
        min_price = self.request.query_params.get('min_price', None)
        max_price = self.request.query_params.get('max_price', None)

        if min_price is not None:
            try:
                queryset = queryset.filter(price__gte=float(min_price))
            except ValueError:
                pass  # Ignore invalid price values

        if max_price is not None:
            try:
                queryset = queryset.filter(price__lte=float(max_price))
            except ValueError:
                pass
        return queryset

    def _apply_stock_range_filters(self, queryset):
        """Apply stock range filters to queryset"""
        min_stock = self.request.query_params.get('min_stock', None)
        max_stock = self.request.query_params.get('max_stock', None)

        if min_stock is not None:
            try:
                queryset = queryset.filter(stock__gte=int(min_stock))
            except ValueError:
                pass

        if max_stock is not None:
            try:
                queryset = queryset.filter(stock__lte=int(max_stock))
            except ValueError:
                pass
        return queryset

    def _apply_ordering(self, queryset):
        """Apply ordering to queryset"""
        ordering = self.request.query_params.get('ordering', None)
        if ordering:
            # Validate ordering field to prevent injection
            allowed_fields = ['name', 'price', 'stock', 'id', '-name', '-price', '-stock', '-id']
            if ordering in allowed_fields:
                queryset = queryset.order_by(ordering)
        else:
            # Default ordering
            queryset = queryset.order_by('name')
        return queryset

    def _apply_limit(self, queryset):
        """Apply limit to queryset"""
        limit = self.request.query_params.get('limit', None)
        if limit is not None:
            try:
                queryset = queryset[:int(limit)]
            except ValueError:
                pass
        return queryset


class ProductDetailAPIView(RetrieveAPIView):
    """
    Generic view for retrieving a single product (read-only)

    RetrieveAPIView provides:
    - GET method to retrieve a single object
    - Automatic 404 handling for non-existent objects
    - Built-in permission checking
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnlyForProducts]  # Read for everyone, write for authenticated
    lookup_field = 'id'  # Default is 'pk', but we can specify any field
    lookup_url_kwarg = 'product_id'  # Match URL parameter name

    def get_object(self):
        """
        Override get_object to add custom logic
        """
        obj = super().get_object()

        # Example: Log product view (in a real app, you might want to track analytics)
        print(f"Product '{obj.name}' was viewed")

        return obj


class UserListAPIView(ListAPIView):
    """
    Generic view for listing users with advanced dynamic filtering

    Available filters:
    - search: Search in username, first_name, last_name, email
    - username: Exact username match
    - email_domain: Filter by email domain
    - is_active: Filter by active status
    - date_joined_after, date_joined_before: Date range filtering
    - ordering: Sort by any field
    - limit: Limit number of results
    """
    serializer_class = UserSerializer
    permission_classes = [IsAdminOrReadOnly]  # Only admins can view user list

    def get_queryset(self):
        """
        Advanced dynamic filtering for users
        """
        queryset = User.objects.all()
        queryset = self._apply_search_filter(queryset)
        queryset = self._apply_username_filter(queryset)
        queryset = self._apply_email_domain_filter(queryset)
        queryset = self._apply_active_status_filter(queryset)
        queryset = self._apply_date_range_filters(queryset)
        queryset = self._apply_ordering(queryset)
        queryset = self._apply_limit(queryset)
        return queryset

    def _apply_search_filter(self, queryset):
        """Apply search filter to queryset"""
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search)
            )
        return queryset

    def _apply_username_filter(self, queryset):
        """Apply username filter to queryset"""
        username = self.request.query_params.get('username', None)
        if username:
            queryset = queryset.filter(username__icontains=username)
        return queryset

    def _apply_email_domain_filter(self, queryset):
        """Apply email domain filter to queryset"""
        email_domain = self.request.query_params.get('email_domain', None)
        if email_domain:
            queryset = queryset.filter(email__endswith=f'@{email_domain}')
        return queryset

    def _apply_active_status_filter(self, queryset):
        """Apply active status filter to queryset"""
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            if is_active.lower() == 'true':
                queryset = queryset.filter(is_active=True)
            elif is_active.lower() == 'false':
                queryset = queryset.filter(is_active=False)
        return queryset

    def _apply_date_range_filters(self, queryset):
        """Apply date range filters to queryset"""
        date_joined_after = self.request.query_params.get('date_joined_after', None)
        date_joined_before = self.request.query_params.get('date_joined_before', None)

        if date_joined_after:
            try:
                date_after = parse_date(date_joined_after)
                if date_after:
                    queryset = queryset.filter(date_joined__gte=date_after)
            except ValueError:
                pass

        if date_joined_before:
            try:
                date_before = parse_date(date_joined_before)
                if date_before:
                    queryset = queryset.filter(date_joined__lte=date_before)
            except ValueError:
                pass
        return queryset

    def _apply_ordering(self, queryset):
        """Apply ordering to queryset"""
        ordering = self.request.query_params.get('ordering', None)
        if ordering:
            allowed_fields = ['username', 'email', 'first_name', 'last_name', 'date_joined',
                            '-username', '-email', '-first_name', '-last_name', '-date_joined']
            if ordering in allowed_fields:
                queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('username')
        return queryset

    def _apply_limit(self, queryset):
        """Apply limit to queryset"""
        limit = self.request.query_params.get('limit', None)
        if limit is not None:
            try:
                queryset = queryset[:int(limit)]
            except ValueError:
                pass
        return queryset


class UserDetailAPIView(RetrieveAPIView):
    """
    Generic view for retrieving a single user
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminOrReadOnly]  # Only admins can view user details
    lookup_field = 'username'  # Use username instead of ID for lookup

    def get_object(self):
        """
        Custom object retrieval with additional context
        """
        obj = super().get_object()

        # Add some context about the user's activity
        obj.recent_orders_count = Order.objects.filter(user=obj).count()

        return obj


class OrderListAPIView(ListAPIView):
    """
    Generic view for listing orders with advanced dynamic filtering and optimized queries

    Available filters:
    - status: Filter by order status (Pending, Confirmed, Cancelled)
    - created_after, created_before: Date range filtering
    - min_total, max_total: Total price range filtering
    - has_items: Filter orders with/without items
    - ordering: Sort by any field
    - limit: Limit number of results
    """
    serializer_class = OrderSerializer
    permission_classes = [IsOrderOwner]  # Users can only access their own orders

    def get_queryset(self):
        """
        Advanced dynamic filtering for orders with optimized queries
        """
        # Use prefetch_related for optimized queries
        queryset = Order.objects.prefetch_related('items__product').filter(user=self.request.user)
        queryset = self._apply_status_filter(queryset)
        queryset = self._apply_date_range_filters(queryset)
        queryset = self._apply_items_filter(queryset)
        queryset = self._apply_ordering(queryset)
        queryset = self._apply_limit(queryset)
        return queryset

    def _apply_status_filter(self, queryset):
        """Apply status filter to queryset"""
        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def _apply_date_range_filters(self, queryset):
        """Apply date range filters to queryset"""
        created_after = self.request.query_params.get('created_after', None)
        created_before = self.request.query_params.get('created_before', None)

        if created_after:
            try:
                date_after = parse_date(created_after)
                if date_after:
                    queryset = queryset.filter(created_at__gte=date_after)
            except ValueError:
                pass

        if created_before:
            try:
                date_before = parse_date(created_before)
                if date_before:
                    queryset = queryset.filter(created_at__lte=date_before)
            except ValueError:
                pass
        return queryset

    def _apply_items_filter(self, queryset):
        """Apply items filter to queryset"""
        has_items = self.request.query_params.get('has_items', None)
        if has_items is not None:
            if has_items.lower() == 'true':
                queryset = queryset.filter(items__isnull=False).distinct()
            elif has_items.lower() == 'false':
                queryset = queryset.filter(items__isnull=True)
        return queryset

    def _apply_ordering(self, queryset):
        """Apply ordering to queryset"""
        ordering = self.request.query_params.get('ordering', None)
        if ordering:
            allowed_fields = ['created_at', 'status', 'order_id', '-created_at', '-status', '-order_id']
            if ordering in allowed_fields:
                queryset = queryset.order_by(ordering)
        else:
            # Default ordering by creation date (newest first)
            queryset = queryset.order_by('-created_at')
        return queryset

    def _apply_limit(self, queryset):
        """Apply limit to queryset"""
        limit = self.request.query_params.get('limit', None)
        if limit is not None:
            try:
                queryset = queryset[:int(limit)]
            except ValueError:
                pass
        return queryset


class OrderDetailAPIView(RetrieveAPIView):
    """
    Generic view for retrieving a single order
    """
    serializer_class = OrderSerializer
    permission_classes = [IsOrderOwner]  # Users can only access their own orders

    def get_queryset(self):
        """
        Ensure users can only view their own orders
        """
        return Order.objects.filter(user=self.request.user)


# Simple function-based view for product information
@api_view(['GET'])
def product_info(request):
    """
    Enhanced API view for product information and statistics with dynamic filtering
    """
    # Get base queryset and apply filters
    products = _apply_product_filters(Product.objects.all(), request)

    # Calculate statistics
    stats = _calculate_product_statistics(products)

    # Prepare data for serializer
    data = {
        'products': products,
        **stats,
        'filters_applied': _get_applied_filters(request)
    }

    serializer = ProductInfoSerializer(data)
    return Response(serializer.data)


def _apply_product_filters(queryset, request):
    """Apply filters to product queryset"""
    queryset = _apply_search_filter(queryset, request)
    queryset = _apply_stock_availability_filter(queryset, request)
    queryset = _apply_price_range_filters(queryset, request)
    return queryset


def _apply_search_filter(queryset, request):
    """Apply search filter to queryset"""
    search = request.query_params.get('search', None)
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )
    return queryset


def _apply_stock_availability_filter(queryset, request):
    """Apply stock availability filter to queryset"""
    in_stock = request.query_params.get('in_stock', None)
    if in_stock is not None:
        if in_stock.lower() == 'true':
            queryset = queryset.filter(stock__gt=0)
        elif in_stock.lower() == 'false':
            queryset = queryset.filter(stock=0)
    return queryset


def _apply_price_range_filters(queryset, request):
    """Apply price range filters to queryset"""
    min_price = request.query_params.get('min_price', None)
    max_price = request.query_params.get('max_price', None)

    if min_price is not None:
        try:
            queryset = queryset.filter(price__gte=float(min_price))
        except ValueError:
            pass

    if max_price is not None:
        try:
            queryset = queryset.filter(price__lte=float(max_price))
        except ValueError:
            pass
    return queryset


def _calculate_product_statistics(products):
    """Calculate product statistics"""
    total_products = products.count()
    in_stock_products = products.filter(stock__gt=0).count()
    out_of_stock_products = total_products - in_stock_products

    # Get price statistics
    price_stats = products.aggregate(
        max_price=Max('price'),
        avg_price=Avg('price'),
        min_price=Max('price')  # We'll fix this below
    )

    # Get actual min price
    min_price_obj = products.order_by('price').first()
    min_price_value = min_price_obj.price if min_price_obj else 0

    # Get stock statistics
    stock_stats = products.aggregate(
        total_stock=Sum('stock'),
        avg_stock=Avg('stock')
    )

    return {
        'count': total_products,
        'max_price': float(price_stats['max_price']) if price_stats['max_price'] else 0,
        'min_price': float(min_price_value),
        'average_price': float(price_stats['avg_price']) if price_stats['avg_price'] else 0,
        'in_stock_count': in_stock_products,
        'out_of_stock_count': out_of_stock_products,
        'total_stock': int(stock_stats['total_stock']) if stock_stats['total_stock'] else 0,
        'average_stock': float(stock_stats['avg_stock']) if stock_stats['avg_stock'] else 0,
    }


def _get_applied_filters(request):
    """Get applied filters from request"""
    return {
        'search': request.query_params.get('search', None),
        'in_stock': request.query_params.get('in_stock', None),
        'min_price': request.query_params.get('min_price', None),
        'max_price': request.query_params.get('max_price', None)
    }
