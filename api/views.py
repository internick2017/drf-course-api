from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from django.db import connection
from django.http import JsonResponse
from django.db.models import Max, Avg
from django.shortcuts import get_object_or_404
import time
import random
from silk.profiling.profiler import silk_profile
from .models import User, Product, Order, OrderItem
from .serializers import UserSerializer, ProductSerializer, OrderSerializer, OrderItemSerializer, ProductInfoSerializer


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for User model"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet for Product model"""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    @action(detail=True, methods=['get'])
    def in_stock(self, request, pk=None):
        """Check if a product is in stock"""
        product = self.get_object()
        return Response({'in_stock': product.in_stock})


class OrderViewSet(viewsets.ModelViewSet):
    """ViewSet for Order model"""
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter orders by current user"""
        return Order.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Set the user to the current user when creating an order"""
        serializer.save(user=self.request.user)


class OrderItemViewSet(viewsets.ModelViewSet):
    """ViewSet for OrderItem model"""
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]


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
    Generic view for listing all products (read-only)

    ListAPIView provides:
    - GET method to retrieve a list of objects
    - Automatic pagination
    - Built-in filtering and ordering capabilities
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        """
        Override get_queryset to add custom filtering
        """
        queryset = Product.objects.all()

        # Filter by stock availability
        in_stock_only = self.request.query_params.get('in_stock', None)
        if in_stock_only is not None:
            if in_stock_only.lower() == 'true':
                queryset = queryset.filter(stock__gt=0)
            elif in_stock_only.lower() == 'false':
                queryset = queryset.filter(stock=0)

        # Filter by price range
        min_price = self.request.query_params.get('min_price', None)
        max_price = self.request.query_params.get('max_price', None)

        if min_price is not None:
            queryset = queryset.filter(price__gte=min_price)
        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)

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
    permission_classes = [IsAuthenticatedOrReadOnly]
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
    Generic view for listing users with custom filtering
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]  # Only authenticated users can view user list

    def get_queryset(self):
        """
        Custom queryset with filtering options
        """
        queryset = User.objects.all()

        # Filter by username (partial match)
        username = self.request.query_params.get('username', None)
        if username:
            queryset = queryset.filter(username__icontains=username)

        # Filter by email domain
        email_domain = self.request.query_params.get('email_domain', None)
        if email_domain:
            queryset = queryset.filter(email__endswith=f'@{email_domain}')

        return queryset


class UserDetailAPIView(RetrieveAPIView):
    """
    Generic view for retrieving a single user
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
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
    Generic view for listing orders with user-specific filtering and optimized queries
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filter orders by current user with optimized queries and status filtering
        """
        # Use prefetch_related for optimized queries (from provided version)
        queryset = Order.objects.prefetch_related('order_items__product').filter(user=self.request.user)

        # Filter by status
        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(status=status)

        # Order by creation date (newest first)
        queryset = queryset.order_by('-created_at')

        return queryset


class OrderDetailAPIView(RetrieveAPIView):
    """
    Generic view for retrieving a single order
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Ensure users can only view their own orders
        """
        return Order.objects.filter(user=self.request.user)


# Simple function-based view for product information
@api_view(['GET'])
def product_info(request):
    """
    API view for product information and statistics using ProductInfoSerializer
    """
    products = Product.objects.all()

    # Calculate statistics
    total_products = products.count()
    in_stock_products = products.filter(stock__gt=0).count()
    out_of_stock_products = total_products - in_stock_products

    # Get price statistics
    price_stats = products.aggregate(
        max_price=Max('price'),
        avg_price=Avg('price')
    )

    # Get min price
    min_price = products.order_by('price').first().price if products.exists() else 0

    # Prepare data for serializer
    data = {
        'products': products,
        'count': total_products,
        'max_price': float(price_stats['max_price']) if price_stats['max_price'] else 0,
        'min_price': float(min_price),
        'average_price': float(price_stats['avg_price']) if price_stats['avg_price'] else 0,
        'in_stock_count': in_stock_products,
        'out_of_stock_count': out_of_stock_products,
    }

    serializer = ProductInfoSerializer(data)
    return Response(serializer.data)
