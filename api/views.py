from rest_framework import viewsets, generics, status, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import (
    ListAPIView, RetrieveAPIView, ListCreateAPIView,
    CreateAPIView, RetrieveUpdateDestroyAPIView
)
from django.db.models import Max, Avg, Q, Sum
from django.utils.dateparse import parse_date
import time
import random
try:
    from silk.profiling.profiler import silk_profile
except ImportError:
    def silk_profile(name=None):
        def decorator(func):
            return func
        return decorator
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter  # type: ignore
from drf_spectacular.types import OpenApiTypes  # type: ignore
from .models import User, Product, Order, OrderItem
from .serializers import UserSerializer, ProductSerializer, OrderSerializer, OrderItemSerializer, ProductInfoSerializer
from .permissions import (
    IsOrderOwner, IsOrderItemOwner,
    IsAdminOrReadOnly, IsAuthenticatedOrReadOnlyForProducts
)
from .filters import UserFilter, ProductFilter, OrderFilter, OrderItemFilter
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


# JWT Authentication Views
@extend_schema(
    summary="User login",
    description="Authenticate user and return JWT tokens",
    tags=["Authentication"],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'username': {'type': 'string', 'description': 'Username'},
                'password': {'type': 'string', 'description': 'Password'},
            },
            'required': ['username', 'password']
        }
    },
    responses={
        200: {
            'description': 'Login successful',
            'type': 'object',
            'properties': {
                'access': {'type': 'string', 'description': 'Access token'},
                'refresh': {'type': 'string', 'description': 'Refresh token'},
                'message': {'type': 'string', 'description': 'Success message'}
            }
        },
        401: {'description': 'Invalid credentials'},
        400: {'description': 'Token error'},
        500: {'description': 'Authentication failed'}
    }
)
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom token obtain view with better error handling and response format
    """
    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
            response.data['message'] = 'Login successful'
            return response
        except (InvalidToken, AuthenticationFailed) as e:
            return Response({
                'error': 'Invalid credentials',
                'detail': str(e)
            }, status=status.HTTP_401_UNAUTHORIZED)
        except TokenError as e:
            return Response({
                'error': 'Token error',
                'detail': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': 'Authentication failed',
                'detail': str(e)
            }, status=status.HTTP_401_UNAUTHORIZED)

@extend_schema(
    summary="User registration",
    description="Register a new user and return JWT tokens",
    tags=["Authentication"],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'username': {'type': 'string', 'description': 'Username'},
                'email': {'type': 'string', 'description': 'Email address'},
                'password': {'type': 'string', 'description': 'Password'},
                'first_name': {'type': 'string', 'description': 'First name'},
                'last_name': {'type': 'string', 'description': 'Last name'},
            },
            'required': ['username', 'email', 'password']
        }
    },
    responses={
        201: {
            'description': 'User registered successfully',
            'type': 'object',
            'properties': {
                'message': {'type': 'string', 'description': 'Success message'},
                'user': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer', 'description': 'User ID'},
                        'username': {'type': 'string', 'description': 'Username'},
                        'email': {'type': 'string', 'description': 'Email'},
                        'is_staff': {'type': 'boolean', 'description': 'Staff status'}
                    }
                },
                'tokens': {
                    'type': 'object',
                    'properties': {
                        'access': {'type': 'string', 'description': 'Access token'},
                        'refresh': {'type': 'string', 'description': 'Refresh token'}
                    }
                }
            }
        },
        400: {'description': 'Registration failed'}
    }
)
class UserRegistrationView(generics.CreateAPIView):
    """
    User registration view with JWT token response
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Validate password
            password = request.data.get('password')
            if password:
                try:
                    validate_password(password)
                except ValidationError as e:
                    return Response({
                        'error': 'Password validation failed',
                        'detail': e.messages
                    }, status=status.HTTP_400_BAD_REQUEST)

            # Create user
            user = serializer.save()
            user.set_password(password)
            user.save()

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)

            return Response({
                'message': 'User registered successfully',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'is_staff': user.is_staff
                },
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                }
            }, status=status.HTTP_201_CREATED)

        return Response({
            'error': 'Registration failed',
            'detail': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(
        summary="List users",
        description="Get a list of all users with advanced filtering options",
        tags=["Users"],
        parameters=[
            OpenApiParameter(name="search", type=OpenApiTypes.STR, description="Search in username, first_name, last_name, email"),
            OpenApiParameter(name="username", type=OpenApiTypes.STR, description="Filter by username"),
            OpenApiParameter(name="email", type=OpenApiTypes.STR, description="Filter by email"),
            OpenApiParameter(name="email_domain", type=OpenApiTypes.STR, description="Filter by email domain"),
            OpenApiParameter(name="is_active", type=OpenApiTypes.BOOL, description="Filter by active status"),
            OpenApiParameter(name="has_orders", type=OpenApiTypes.BOOL, description="Filter users who have placed orders"),
            OpenApiParameter(name="ordering", type=OpenApiTypes.STR, description="Order by field (username, email, date_joined)"),
        ]
    ),
    create=extend_schema(
        summary="Create user",
        description="Create a new user (Admin only)",
        tags=["Users"]
    ),
    retrieve=extend_schema(
        summary="Get user details",
        description="Get detailed information about a specific user",
        tags=["Users"]
    ),
    update=extend_schema(
        summary="Update user",
        description="Update user information (Admin only)",
        tags=["Users"]
    ),
    destroy=extend_schema(
        summary="Delete user",
        description="Delete a user (Admin only)",
        tags=["Users"]
    )
)
class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for User model with advanced filtering and Django filtering"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminOrReadOnly]  # Only admins can manage users
    filterset_class = UserFilter
    search_fields = ['username', 'first_name', 'last_name', 'email']
    ordering_fields = ['username', 'email', 'first_name', 'last_name', 'date_joined']
    ordering = ['username']

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


@extend_schema_view(
    list=extend_schema(
        summary="List products",
        description="Get a list of all products with advanced filtering options",
        tags=["Products"],
        parameters=[
            OpenApiParameter(name="search", type=OpenApiTypes.STR, description="Search in name and description"),
            OpenApiParameter(name="name", type=OpenApiTypes.STR, description="Filter by product name"),
            OpenApiParameter(name="in_stock", type=OpenApiTypes.BOOL, description="Filter products in stock"),
            OpenApiParameter(name="out_of_stock", type=OpenApiTypes.BOOL, description="Filter products out of stock"),
            OpenApiParameter(name="price_min", type=OpenApiTypes.NUMBER, description="Minimum price"),
            OpenApiParameter(name="price_max", type=OpenApiTypes.NUMBER, description="Maximum price"),
            OpenApiParameter(name="stock_min", type=OpenApiTypes.INT, description="Minimum stock"),
            OpenApiParameter(name="stock_max", type=OpenApiTypes.INT, description="Maximum stock"),
            OpenApiParameter(name="has_orders", type=OpenApiTypes.BOOL, description="Filter products that have been ordered"),
            OpenApiParameter(name="ordering", type=OpenApiTypes.STR, description="Order by field (name, price, stock, created_at)"),
        ]
    ),
    create=extend_schema(
        summary="Create product",
        description="Create a new product (Authenticated users only)",
        tags=["Products"]
    ),
    retrieve=extend_schema(
        summary="Get product details",
        description="Get detailed information about a specific product",
        tags=["Products"]
    ),
    update=extend_schema(
        summary="Update product",
        description="Update product information (Authenticated users only)",
        tags=["Products"]
    ),
    destroy=extend_schema(
        summary="Delete product",
        description="Delete a product (Authenticated users only)",
        tags=["Products"]
    )
)
class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet for Product model with advanced filtering and Django filtering"""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnlyForProducts]  # Read for everyone, write for authenticated
    filterset_class = ProductFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'price', 'stock', 'created_at']
    ordering = ['name']

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


@extend_schema_view(
    list=extend_schema(
        summary="List orders",
        description="Get a list of orders with advanced filtering options",
        tags=["Orders"],
        parameters=[
            OpenApiParameter(name="order_id", type=OpenApiTypes.STR, description="Filter by order ID"),
            OpenApiParameter(name="user_username", type=OpenApiTypes.STR, description="Filter by user username"),
            OpenApiParameter(name="user_email", type=OpenApiTypes.STR, description="Filter by user email"),
            OpenApiParameter(name="status", type=OpenApiTypes.STR, description="Filter by order status"),
            OpenApiParameter(name="has_items", type=OpenApiTypes.BOOL, description="Filter orders with items"),

            OpenApiParameter(name="created_after", type=OpenApiTypes.DATE, description="Created after date"),
            OpenApiParameter(name="created_before", type=OpenApiTypes.DATE, description="Created before date"),
            OpenApiParameter(name="ordering", type=OpenApiTypes.STR, description="Order by field (created_at, status, order_id)"),
        ]
    ),
    create=extend_schema(
        summary="Create order",
        description="Create a new order",
        tags=["Orders"]
    ),
    retrieve=extend_schema(
        summary="Get order details",
        description="Get detailed information about a specific order",
        tags=["Orders"]
    ),
    update=extend_schema(
        summary="Update order",
        description="Update order information",
        tags=["Orders"]
    ),
    destroy=extend_schema(
        summary="Delete order",
        description="Delete an order",
        tags=["Orders"]
    )
)
class OrderViewSet(viewsets.ModelViewSet):
    """ViewSet for Order model with advanced filtering and Django filtering"""
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsOrderOwner]  # Users can only access their own orders
    filterset_class = OrderFilter
    search_fields = ['order_id', 'user__username', 'user__email']
    ordering_fields = ['created_at', 'status', 'order_id']
    ordering = ['-created_at']

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


@extend_schema_view(
    list=extend_schema(
        summary="List order items",
        description="Get a list of order items with advanced filtering options",
        tags=["Order Items"],
        parameters=[
            OpenApiParameter(name="order_id", type=OpenApiTypes.STR, description="Filter by order ID"),
            OpenApiParameter(name="product_name", type=OpenApiTypes.STR, description="Filter by product name"),
            OpenApiParameter(name="product_id", type=OpenApiTypes.INT, description="Filter by product ID"),
            OpenApiParameter(name="user_username", type=OpenApiTypes.STR, description="Filter by user username"),
            OpenApiParameter(name="quantity_min", type=OpenApiTypes.INT, description="Minimum quantity"),
            OpenApiParameter(name="quantity_max", type=OpenApiTypes.INT, description="Maximum quantity"),

            OpenApiParameter(name="ordering", type=OpenApiTypes.STR, description="Order by field (quantity, product__name, order__created_at)"),
        ]
    ),
    create=extend_schema(
        summary="Create order item",
        description="Create a new order item",
        tags=["Order Items"]
    ),
    retrieve=extend_schema(
        summary="Get order item details",
        description="Get detailed information about a specific order item",
        tags=["Order Items"]
    ),
    update=extend_schema(
        summary="Update order item",
        description="Update order item information",
        tags=["Order Items"]
    ),
    destroy=extend_schema(
        summary="Delete order item",
        description="Delete an order item",
        tags=["Order Items"]
    )
)
class OrderItemViewSet(viewsets.ModelViewSet):
    """ViewSet for OrderItem model with advanced filtering and Django filtering"""
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    permission_classes = [IsOrderItemOwner]  # Users can only access their own order items
    filterset_class = OrderItemFilter
    search_fields = ['order__order_id', 'product__name']
    ordering_fields = ['quantity', 'product__name', 'order__created_at']
    ordering = ['-order__created_at']

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


@extend_schema(
    summary="Profiling example",
    description="Demonstrate django-silk profiling techniques with different performance scenarios",
    tags=["Profiling"],
    responses={
        200: {
            'description': 'Profiling data',
            'type': 'object',
            'properties': {
                'message': {'type': 'string'},
                'expensive_calculation_result': {'type': 'number'},
                'database_stats': {
                    'type': 'object',
                    'properties': {
                        'user_count': {'type': 'integer'},
                        'product_count': {'type': 'integer'},
                        'order_count': {'type': 'integer'}
                    }
                },
                'manual_timing': {'type': 'number'},
                'total_request_time': {'type': 'number'},
                'profiling_info': {
                    'type': 'object',
                    'properties': {
                        'silk_enabled': {'type': 'boolean'},
                        'profiling_url': {'type': 'string'},
                        'note': {'type': 'string'}
                    }
                }
            }
        }
    }
)
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


@extend_schema(
    summary="Performance test",
    description="Compare N+1 vs optimized queries for performance analysis",
    tags=["Profiling"],
    parameters=[
        OpenApiParameter(
            name="test",
            type=OpenApiTypes.STR,
            description="Test type: 'n_plus_one', 'optimized', or 'both' (default)",
            required=False
        )
    ],
    responses={
        200: {
            'description': 'Performance test results',
            'type': 'object',
            'properties': {
                'test_type': {'type': 'string'},
                'data': {'type': 'array'},
                'note': {'type': 'string'},
                'n_plus_one_test': {'type': 'object'},
                'optimized_test': {'type': 'object'},
                'comparison_note': {'type': 'string'}
            }
        }
    }
)
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


# Enhanced Generic Views for List and Create Operations

class ProductListCreateAPIView(ListCreateAPIView):
    """
    Generic view for listing and creating products

    GET: List all products with advanced filtering
    POST: Create a new product (Admin only)

    Available filters for GET:
    - search: Search in name and description
    - in_stock: true/false for stock availability
    - min_price, max_price: Price range filtering
    - min_stock, max_stock: Stock range filtering
    - ordering: Sort by any field (name, price, stock, id)
    - limit: Limit number of results

    POST data format:
    {
        "name": "Product Name",
        "description": "Product description",
        "price": "99.99",
        "stock": 10,
        "image": "image_file" (optional)
    }
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        """Apply advanced filtering for product listing"""
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

    def _apply_limit(self, queryset):
        """Apply limit to queryset"""
        limit = self.request.query_params.get('limit', None)
        if limit is not None:
            try:
                queryset = queryset[:int(limit)]
            except ValueError:
                pass
        return queryset

    def perform_create(self, serializer):
        """Custom logic when creating a product"""
        product = serializer.save()
        print(f"New product created: {product.name} with price ${product.price}")


class ProductCreateAPIView(CreateAPIView):
    """
    Generic view for creating products only (POST only) - Admin only

    POST data format:
    {
        "name": "Product Name",
        "description": "Product description",
        "price": "99.99",
        "stock": 10,
        "image": "image_file" (optional)
    }
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]

    def perform_create(self, serializer):
        """Custom logic when creating a product"""
        product = serializer.save()
        print(f"Product created via CreateAPIView: {product.name}")


class ProductRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    """
    Generic view for retrieving, updating, and deleting a single product

    GET: Retrieve product details
    PUT/PATCH: Update product (Admin only)
    DELETE: Delete product (Admin only)

    Available URL parameters:
    - pk: Product ID
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'id'

    def perform_update(self, serializer):
        """Custom logic when updating a product"""
        product = serializer.save()
        print(f"Product updated: {product.name}")

    def perform_destroy(self, instance):
        """Custom logic when deleting a product"""
        print(f"Product deleted: {instance.name}")
        instance.delete()


class UserListCreateAPIView(ListCreateAPIView):
    """
    Generic view for listing and creating users (Admin only)

    GET: List all users with advanced filtering
    POST: Create a new user

    Available filters for GET:
    - search: Search in username, first_name, last_name, email
    - username: Exact username match
    - email_domain: Filter by email domain
    - is_active: Filter by active status
    - date_joined_after, date_joined_before: Date range filtering
    - ordering: Sort by any field
    - limit: Limit number of results

    POST data format:
    {
        "username": "newuser",
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "password": "securepassword"
    }
    """
    serializer_class = UserSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        """Apply advanced filtering for user listing"""
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

    def perform_create(self, serializer):
        """Custom logic when creating a user"""
        user = serializer.save()
        print(f"New user created: {user.username}")


class OrderListCreateAPIView(ListCreateAPIView):
    """
    Generic view for listing and creating orders

    GET: List user's orders with advanced filtering
    POST: Create a new order for the current user (Admin only)

    Available filters for GET:
    - status: Filter by order status (Pending, Confirmed, Cancelled)
    - created_after, created_before: Date range filtering
    - has_items: Filter orders with/without items
    - ordering: Sort by any field
    - limit: Limit number of results

    POST data format:
    {
        "status": "Pending" (optional, defaults to "Pending")
    }
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        """Apply advanced filtering for order listing"""
        # Admins can see all orders, regular users see only their own
        if self.request.user.is_staff:
            queryset = Order.objects.prefetch_related('items__product').all()
        else:
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

    def perform_create(self, serializer):
        """Set the user to the current user when creating an order"""
        order = serializer.save(user=self.request.user)
        print(f"New order created: {order.order_id} for user {self.request.user.username}")


class OrderItemListCreateAPIView(ListCreateAPIView):
    """
    Generic view for listing and creating order items

    GET: List order items with advanced filtering
    POST: Create a new order item (Admin only)

    Available filters for GET:
    - order_id: Filter by order ID
    - product_id: Filter by product ID
    - min_quantity, max_quantity: Quantity range filtering
    - ordering: Sort by any field
    - limit: Limit number of results

    POST data format:
    {
        "order": "order_uuid",
        "product": "product_id",
        "quantity": 2
    }
    """
    serializer_class = OrderItemSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        """Apply advanced filtering for order item listing"""
        # Admins can see all order items, regular users see only their own
        if self.request.user.is_staff:
            queryset = OrderItem.objects.select_related('order', 'product').all()
        else:
            queryset = OrderItem.objects.select_related('order', 'product').filter(order__user=self.request.user)

        queryset = self._apply_order_filter(queryset)
        queryset = self._apply_product_filter(queryset)
        queryset = self._apply_quantity_range_filters(queryset)
        queryset = self._apply_ordering(queryset)
        queryset = self._apply_limit(queryset)
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

    def _apply_limit(self, queryset):
        """Apply limit to queryset"""
        limit = self.request.query_params.get('limit', None)
        if limit is not None:
            try:
                queryset = queryset[:int(limit)]
            except ValueError:
                pass
        return queryset

    def perform_create(self, serializer):
        """Custom logic when creating an order item"""
        order_item = serializer.save()
        print(f"New order item created: {order_item.quantity}x {order_item.product.name}")


# Simple Create-only views for specific use cases

class ProductCreateOnlyAPIView(CreateAPIView):
    """
    Create-only view for products (useful for forms or specific workflows) - Admin only
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]

    def perform_create(self, serializer):
        """Custom logic when creating a product"""
        product = serializer.save()
        print(f"Product created via CreateOnly view: {product.name}")


class OrderCreateOnlyAPIView(CreateAPIView):
    """
    Create-only view for orders (useful for checkout process) - Admin only
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAdminOrReadOnly]

    def perform_create(self, serializer):
        """Set the user to the current user when creating an order"""
        order = serializer.save(user=self.request.user)
        print(f"Order created via CreateOnly view: {order.order_id}")


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


# Additional Update and Delete Generic Views

class UserRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    """
    Generic view for retrieving, updating, and deleting a single user

    GET: Retrieve user details
    PUT/PATCH: Update user (Admin only)
    DELETE: Delete user (Admin only)

    Available URL parameters:
    - username: Username to identify the user
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'username'

    def perform_update(self, serializer):
        """Custom logic when updating a user"""
        user = serializer.save()
        print(f"User updated: {user.username}")

    def perform_destroy(self, instance):
        """Custom logic when deleting a user"""
        print(f"User deleted: {instance.username}")
        instance.delete()


class OrderRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    """
    Generic view for retrieving, updating, and deleting a single order

    GET: Retrieve order details
    PUT/PATCH: Update order (Admin only)
    DELETE: Delete order (Admin only)

    Available URL parameters:
    - pk: Order UUID
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'pk'

    def get_queryset(self):
        """Apply user-specific filtering for orders"""
        # Admins can see all orders, regular users see only their own
        if self.request.user.is_staff:
            return Order.objects.prefetch_related('items__product').all()
        else:
            return Order.objects.prefetch_related('items__product').filter(user=self.request.user)

    def perform_update(self, serializer):
        """Custom logic when updating an order"""
        order = serializer.save()
        print(f"Order updated: {order.order_id}")

    def perform_destroy(self, instance):
        """Custom logic when deleting an order"""
        print(f"Order deleted: {instance.order_id}")
        instance.delete()


class OrderItemRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    """
    Generic view for retrieving, updating, and deleting a single order item

    GET: Retrieve order item details
    PUT/PATCH: Update order item (Admin only)
    DELETE: Delete order item (Admin only)

    Available URL parameters:
    - pk: Order item ID
    """
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        """Apply user-specific filtering for order items"""
        # Admins can see all order items, regular users see only their own
        if self.request.user.is_staff:
            return OrderItem.objects.select_related('order', 'product').all()
        else:
            return OrderItem.objects.select_related('order', 'product').filter(order__user=self.request.user)

    def perform_update(self, serializer):
        """Custom logic when updating an order item"""
        order_item = serializer.save()
        print(f"Order item updated: {order_item.quantity}x {order_item.product.name}")

    def perform_destroy(self, instance):
        """Custom logic when deleting an order item"""
        print(f"Order item deleted: {instance.quantity}x {instance.product.name}")
        instance.delete()
