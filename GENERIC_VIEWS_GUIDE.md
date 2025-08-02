# Django REST Framework - Generic Views Guide

## Overview

Django REST Framework provides several generic views that simplify common API patterns. This guide focuses on **ListAPIView** and **RetrieveAPIView**, which are read-only views for listing and retrieving objects.

## ListAPIView

**ListAPIView** is a generic view that provides a read-only endpoint for listing a collection of objects.

### Key Features:
- **HTTP Method**: GET only
- **Purpose**: Retrieve a list of objects
- **Automatic Features**: Pagination, filtering, ordering
- **Customizable**: Override `get_queryset()` for custom filtering

### Example Implementation:

```python
class ProductListAPIView(ListAPIView):
    """
    Generic view for listing all products (read-only)
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
```

### URL Pattern:
```python
path('generic/products/', ProductListAPIView.as_view(), name='product-list-generic')
```

### Usage Examples:
```bash
# Get all products
GET /api/generic/products/

# Get only products in stock
GET /api/generic/products/?in_stock=true

# Get products with price between 10 and 100
GET /api/generic/products/?min_price=10&max_price=100

# Get products out of stock
GET /api/generic/products/?in_stock=false
```

## RetrieveAPIView

**RetrieveAPIView** is a generic view that provides a read-only endpoint for retrieving a single object.

### Key Features:
- **HTTP Method**: GET only
- **Purpose**: Retrieve a single object by ID
- **Automatic Features**: 404 handling, permission checking
- **Customizable**: Override `get_object()` for custom logic

### Example Implementation:

```python
class ProductDetailAPIView(RetrieveAPIView):
    """
    Generic view for retrieving a single product (read-only)
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'id'  # Default is 'pk', but we can specify any field

    def get_object(self):
        """
        Override get_object to add custom logic
        """
        obj = super().get_object()

        # Example: Log product view (in a real app, you might want to track analytics)
        print(f"Product '{obj.name}' was viewed")

        return obj
```

### URL Pattern:
```python
path('generic/products/<int:id>/', ProductDetailAPIView.as_view(), name='product-detail-generic')
```

### Usage Examples:
```bash
# Get product with ID 1
GET /api/generic/products/1/

# Get product with ID 5
GET /api/generic/products/5/
```

## Advanced Examples

### User List with Custom Filtering

```python
class UserListAPIView(ListAPIView):
    """
    Generic view for listing users with custom filtering
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

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
```

### User Detail with Custom Lookup Field

```python
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
```

### Order List with User-Specific Filtering

```python
class OrderListAPIView(ListAPIView):
    """
    Generic view for listing orders with user-specific filtering
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filter orders by current user and add status filtering
        """
        queryset = Order.objects.filter(user=self.request.user)

        # Filter by status
        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(status=status)

        # Order by creation date (newest first)
        queryset = queryset.order_by('-created_at')

        return queryset
```

## Key Differences from ViewSets

| Feature | ListAPIView | RetrieveAPIView | ViewSet |
|---------|-------------|-----------------|---------|
| **HTTP Methods** | GET only | GET only | GET, POST, PUT, PATCH, DELETE |
| **Purpose** | List objects | Single object | Full CRUD operations |
| **Complexity** | Simple | Simple | More complex |
| **Customization** | Limited | Limited | Highly customizable |
| **Use Case** | Read-only lists | Read-only details | Full API endpoints |

## Best Practices

### 1. Use ListAPIView when:
- You only need to list objects
- You want simple filtering and pagination
- You don't need create/update/delete operations

### 2. Use RetrieveAPIView when:
- You only need to retrieve single objects
- You want automatic 404 handling
- You need custom object retrieval logic

### 3. Override Methods:
- `get_queryset()`: For custom filtering and ordering
- `get_object()`: For custom object retrieval logic
- `get_serializer_context()`: For adding context to serializers

### 4. Security:
- Always set appropriate `permission_classes`
- Filter querysets by user when needed
- Validate lookup fields

## Testing the Generic Views

### Start the Development Server:
```bash
python manage.py runserver
```

### Test ListAPIView:
```bash
# Get all products
curl http://localhost:8000/api/generic/products/

# Filter products in stock
curl http://localhost:8000/api/generic/products/?in_stock=true

# Filter by price range
curl http://localhost:8000/api/generic/products/?min_price=10&max_price=50
```

### Test RetrieveAPIView:
```bash
# Get specific product
curl http://localhost:8000/api/generic/products/1/

# Get user by username
curl http://localhost:8000/api/generic/users/admin/
```

## Comparison with ViewSets

### ViewSet Approach (Existing):
```python
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
```

**URLs**: `/api/products/` (GET, POST, PUT, PATCH, DELETE)

### Generic View Approach (New):
```python
class ProductListAPIView(ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
```

**URLs**: `/api/generic/products/` (GET only)

## Conclusion

Generic views like **ListAPIView** and **RetrieveAPIView** are perfect for:
- **Simple read-only APIs**
- **Microservices** that only need to expose data
- **Public APIs** where you want to limit operations
- **Performance optimization** by reducing unnecessary endpoints

They provide a clean, simple way to create read-only endpoints while maintaining all the benefits of Django REST Framework's serialization, permissions, and pagination.