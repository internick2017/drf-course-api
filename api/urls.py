from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, ProductViewSet, OrderViewSet, OrderItemViewSet,
    ProfilingExampleView, PerformanceTestView,
    # Generic Views
    ProductListAPIView, ProductDetailAPIView,
    UserListAPIView, UserDetailAPIView,
    OrderListAPIView, OrderDetailAPIView,
    # New Enhanced Generic Views
    ProductListCreateAPIView, ProductCreateAPIView, ProductRetrieveUpdateDestroyAPIView,
    UserListCreateAPIView, OrderListCreateAPIView, OrderItemListCreateAPIView,
    ProductCreateOnlyAPIView, OrderCreateOnlyAPIView,
    # Additional Update and Delete Generic Views
    UserRetrieveUpdateDestroyAPIView, OrderRetrieveUpdateDestroyAPIView, OrderItemRetrieveUpdateDestroyAPIView,
    # JWT Authentication Views
    CustomTokenObtainPairView, UserRegistrationView,
    # Simple function-based view
    product_info
)

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'products', ProductViewSet)
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'order-items', OrderItemViewSet)

# The API URLs are now determined automatically by the router
urlpatterns = [
    # JWT Authentication URLs
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='auth-login'),
    path('auth/register/', UserRegistrationView.as_view(), name='auth-register'),

    # ViewSet URLs (Full CRUD functionality)
    path('', include(router.urls)),

    # Simple URLs for easier access (matching your provided structure)
    path('products/', ProductListAPIView.as_view(), name='products-simple'),
    path('products/info/', product_info, name='product-info'),
    path('products/<int:product_id>/', ProductDetailAPIView.as_view(), name='product-detail-simple'),
    path('orders/', OrderListAPIView.as_view(), name='orders-simple'),

    # Profiling and Performance Testing
    path('profiling-example/', ProfilingExampleView.as_view(), name='profiling-example'),
    path('performance-test/', PerformanceTestView.as_view(), name='performance-test'),

    # Generic Views URLs - Demonstrating ListAPIView & RetrieveAPIView
    # Products
    path('generic/products/', ProductListAPIView.as_view(), name='product-list-generic'),
    path('generic/products/<int:id>/', ProductDetailAPIView.as_view(), name='product-detail-generic'),

    # Users
    path('generic/users/', UserListAPIView.as_view(), name='user-list-generic'),
    path('generic/users/<str:username>/', UserDetailAPIView.as_view(), name='user-detail-generic'),

    # Orders
    path('generic/orders/', OrderListAPIView.as_view(), name='order-list-generic'),
    path('generic/orders/<uuid:pk>/', OrderDetailAPIView.as_view(), name='order-detail-generic'),

    # Enhanced Generic Views - ListCreateAPIView, CreateAPIView, RetrieveUpdateDestroyAPIView
    # Products with List and Create functionality
    path('enhanced/products/', ProductListCreateAPIView.as_view(), name='product-list-create'),
    path('enhanced/products/create/', ProductCreateAPIView.as_view(), name='product-create-only'),
    path('enhanced/products/<int:id>/', ProductRetrieveUpdateDestroyAPIView.as_view(), name='product-retrieve-update-destroy'),
    path('enhanced/products/create-only/', ProductCreateOnlyAPIView.as_view(), name='product-create-only-simple'),

    # Users with List, Create, Update, and Delete functionality
    path('enhanced/users/', UserListCreateAPIView.as_view(), name='user-list-create'),
    path('enhanced/users/<str:username>/', UserRetrieveUpdateDestroyAPIView.as_view(), name='user-retrieve-update-destroy'),

    # Orders with List, Create, Update, and Delete functionality
    path('enhanced/orders/', OrderListCreateAPIView.as_view(), name='order-list-create'),
    path('enhanced/orders/<uuid:pk>/', OrderRetrieveUpdateDestroyAPIView.as_view(), name='order-retrieve-update-destroy'),
    path('enhanced/orders/create-only/', OrderCreateOnlyAPIView.as_view(), name='order-create-only'),

    # Order Items with List, Create, Update, and Delete functionality
    path('enhanced/order-items/', OrderItemListCreateAPIView.as_view(), name='order-item-list-create'),
    path('enhanced/order-items/<int:pk>/', OrderItemRetrieveUpdateDestroyAPIView.as_view(), name='order-item-retrieve-update-destroy'),
]