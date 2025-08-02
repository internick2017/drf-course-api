from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, ProductViewSet, OrderViewSet, OrderItemViewSet,
    ProfilingExampleView, PerformanceTestView,
    # Generic Views
    ProductListAPIView, ProductDetailAPIView,
    UserListAPIView, UserDetailAPIView,
    OrderListAPIView, OrderDetailAPIView,
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
]