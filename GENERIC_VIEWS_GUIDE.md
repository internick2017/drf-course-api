# Django REST Framework Generic Views Guide

This guide explains the implementation of generic views in our Django REST Framework API, focusing on **List** and **Create** operations using various generic view classes.

## Overview

Generic views provide a way to quickly build common API patterns without writing boilerplate code. We've implemented several types of generic views to demonstrate different use cases.

**⚠️ Important Note**: All **create, update, and delete operations** require **administrator privileges**. Regular users can only perform **read operations** (GET requests).

## Types of Generic Views Implemented

### 1. ListCreateAPIView
Combines **GET** (list) and **POST** (create) operations in a single view.

### 2. CreateAPIView
Provides **POST** (create) functionality only.

### 3. ListAPIView
Provides **GET** (list) functionality only.

### 4. RetrieveAPIView
Provides **GET** (retrieve single object) functionality only.

### 5. RetrieveUpdateDestroyAPIView
Provides **GET**, **PUT/PATCH**, and **DELETE** operations for a single object.

## Available Generic Views

### Product Views

#### ProductListCreateAPIView
- **URL**: `/api/enhanced/products/`
- **Methods**: GET, POST
- **Description**: List all products and create new products (Admin only for POST)

**GET Request Examples:**
```bash
# List all products
GET /api/enhanced/products/

# Search products
GET /api/enhanced/products/?search=laptop

# Filter by stock availability
GET /api/enhanced/products/?in_stock=true

# Filter by price range
GET /api/enhanced/products/?min_price=50&max_price=200

# Filter by stock range
GET /api/enhanced/products/?min_stock=5&max_stock=50

# Order by price (ascending)
GET /api/enhanced/products/?ordering=price

# Order by price (descending)
GET /api/enhanced/products/?ordering=-price

# Limit results
GET /api/enhanced/products/?limit=10
```

**POST Request Example:**
```bash
POST /api/enhanced/products/
Content-Type: application/json

{
    "name": "New Product",
    "description": "Product description",
    "price": "99.99",
    "stock": 10
}
```

#### ProductCreateAPIView
- **URL**: `/api/enhanced/products/create/`
- **Methods**: POST only
- **Description**: Create-only endpoint for products (Admin only)

#### ProductRetrieveUpdateDestroyAPIView
- **URL**: `/api/enhanced/products/{id}/`
- **Methods**: GET, PUT, PATCH, DELETE
- **Description**: Full CRUD operations for a single product (Admin only for write operations)

**Example:**
```bash
# Get product details
GET /api/enhanced/products/1/

# Update product
PUT /api/enhanced/products/1/
{
    "name": "Updated Product",
    "description": "Updated description",
    "price": "149.99",
    "stock": 15
}

# Delete product
DELETE /api/enhanced/products/1/
```

### User Views

#### UserListCreateAPIView
- **URL**: `/api/enhanced/users/`
- **Methods**: GET, POST
- **Description**: List all users and create new users (Admin only)

**GET Request Examples:**
```bash
# List all users
GET /api/enhanced/users/

# Search users
GET /api/enhanced/users/?search=john

# Filter by email domain
GET /api/enhanced/users/?email_domain=gmail.com

# Filter by active status
GET /api/enhanced/users/?is_active=true

# Filter by date range
GET /api/enhanced/users/?date_joined_after=2023-01-01&date_joined_before=2023-12-31

# Order by username
GET /api/enhanced/users/?ordering=username

# Limit results
GET /api/enhanced/users/?limit=20
```

**POST Request Example:**
```bash
POST /api/enhanced/users/
Content-Type: application/json

{
    "username": "newuser",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "password": "securepassword123"
}
```

### Order Views

#### OrderListCreateAPIView
- **URL**: `/api/enhanced/orders/`
- **Methods**: GET, POST
- **Description**: List user's orders and create new orders (Admin only for POST)

**GET Request Examples:**
```bash
# List user's orders
GET /api/enhanced/orders/

# Filter by status
GET /api/enhanced/orders/?status=Pending

# Filter by date range
GET /api/enhanced/orders/?created_after=2023-01-01&created_before=2023-12-31

# Filter orders with items
GET /api/enhanced/orders/?has_items=true

# Order by creation date (newest first)
GET /api/enhanced/orders/?ordering=-created_at

# Limit results
GET /api/enhanced/orders/?limit=5
```

**POST Request Example:**
```bash
POST /api/enhanced/orders/
Content-Type: application/json

{
    "status": "Pending"
}
```

#### OrderCreateOnlyAPIView
- **URL**: `/api/enhanced/orders/create-only/`
- **Methods**: POST only
- **Description**: Create-only endpoint for orders (Admin only)

### Order Item Views

#### OrderItemListCreateAPIView
- **URL**: `/api/enhanced/order-items/`
- **Methods**: GET, POST
- **Description**: List order items and create new order items (Admin only for POST)

**GET Request Examples:**
```bash
# List all order items
GET /api/enhanced/order-items/

# Filter by order ID
GET /api/enhanced/order-items/?order_id=uuid-here

# Filter by product ID
GET /api/enhanced/order-items/?product_id=1

# Filter by quantity range
GET /api/enhanced/order-items/?min_quantity=2&max_quantity=10

# Order by quantity
GET /api/enhanced/order-items/?ordering=quantity

# Limit results
GET /api/enhanced/order-items/?limit=10
```

**POST Request Example:**
```bash
POST /api/enhanced/order-items/
Content-Type: application/json

{
    "order": "order-uuid-here",
    "product": 1,
    "quantity": 2
}
```

## URL Structure

```
/api/
├── enhanced/
│   ├── products/
│   │   ├── /                    # ListCreateAPIView (GET, POST)
│   │   ├── create/              # CreateAPIView (POST only)
│   │   ├── create-only/         # CreateOnlyAPIView (POST only)
│   │   └── {id}/                # RetrieveUpdateDestroyAPIView (GET, PUT, PATCH, DELETE)
│   ├── users/
│   │   └── /                    # ListCreateAPIView (GET, POST)
│   ├── orders/
│   │   ├── /                    # ListCreateAPIView (GET, POST)
│   │   └── create-only/         # CreateOnlyAPIView (POST only)
│   └── order-items/
│       └── /                    # ListCreateAPIView (GET, POST)
├── generic/                     # Original generic views
└── ...                         # ViewSet endpoints
```

## Key Features

### 1. Advanced Filtering
All list views support comprehensive filtering:
- **Search**: Text search across relevant fields
- **Range filters**: Min/max values for numeric fields
- **Boolean filters**: True/false for boolean fields
- **Date range filters**: Before/after dates
- **Exact match filters**: Specific field values

### 2. Ordering
All list views support ordering by any field:
- **Ascending**: `?ordering=field_name`
- **Descending**: `?ordering=-field_name`

### 3. Pagination/Limiting
All list views support result limiting:
- **Limit**: `?limit=10`

### 4. Permission Control
Each view has appropriate permissions:
- **Products**: Read for everyone, write for admin users only
- **Users**: Admin only
- **Orders**: Read for users (their own orders) and admins (all orders), write for admin users only
- **Order Items**: Read for users (their own order items) and admins (all order items), write for admin users only

### 5. Custom Logic
Each view includes custom logic in `perform_create()` method:
- **Products**: Logs creation with name and price
- **Users**: Logs creation with username
- **Orders**: Automatically assigns current user
- **Order Items**: Logs creation with quantity and product name

## Testing the Generic Views

### Using curl

```bash
# List products
curl -X GET "http://localhost:8000/api/enhanced/products/"

# Create a product (Admin only)
curl -X POST "http://localhost:8000/api/enhanced/products/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer admin-token" \
  -d '{
    "name": "Test Product",
    "description": "Test description",
    "price": "29.99",
    "stock": 5
  }'

# Get product details
curl -X GET "http://localhost:8000/api/enhanced/products/1/"

# Update product (Admin only)
curl -X PUT "http://localhost:8000/api/enhanced/products/1/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer admin-token" \
  -d '{
    "name": "Updated Product",
    "description": "Updated description",
    "price": "39.99",
    "stock": 10
  }'

# Delete product (Admin only)
curl -X DELETE "http://localhost:8000/api/enhanced/products/1/" \
  -H "Authorization: Bearer admin-token"
```

### Using Python requests

```python
import requests

# Base URL
base_url = "http://localhost:8000/api/enhanced"

# Headers
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer admin-token"  # Admin token required for write operations
}

# List products
response = requests.get(f"{base_url}/products/")
products = response.json()

# Create product
product_data = {
    "name": "Python Product",
    "description": "Created via Python",
    "price": "49.99",
    "stock": 15
}
response = requests.post(f"{base_url}/products/", json=product_data, headers=headers)
new_product = response.json()

# Get product details
product_id = new_product['id']
response = requests.get(f"{base_url}/products/{product_id}/")
product = response.json()

# Update product
update_data = {
    "name": "Updated Python Product",
    "description": "Updated via Python",
    "price": "59.99",
    "stock": 20
}
response = requests.put(f"{base_url}/products/{product_id}/", json=update_data, headers=headers)

# Delete product
response = requests.delete(f"{base_url}/products/{product_id}/", headers=headers)
```

## Benefits of Generic Views

1. **Less Code**: No need to write boilerplate CRUD operations
2. **Consistency**: Standardized API patterns across the application
3. **Maintainability**: Centralized logic for common operations
4. **Flexibility**: Easy to customize with custom methods and logic
5. **Performance**: Optimized queries with select_related and prefetch_related
6. **Security**: Built-in permission checking and validation

## Best Practices

1. **Use appropriate permissions**: Always set permission_classes
2. **Override perform_create()**: Add custom logic when creating objects
3. **Use filtering**: Implement get_queryset() for dynamic filtering
4. **Validate input**: Use serializer validation for data integrity
5. **Optimize queries**: Use select_related and prefetch_related for related objects
6. **Document your API**: Use docstrings to explain functionality

## Comparison with ViewSets

| Feature | Generic Views | ViewSets |
|---------|---------------|----------|
| **Flexibility** | High - customize each operation | Medium - predefined patterns |
| **Code Reuse** | Low - separate classes | High - single class |
| **Complexity** | Simple - focused operations | Complex - full CRUD |
| **URLs** | Manual - explicit patterns | Automatic - router generated |
| **Use Case** | Specific operations | Full resource management |

Choose generic views when you need:
- Specific operations (list + create only)
- Custom logic for each operation
- Explicit URL patterns
- Simple, focused functionality

Choose ViewSets when you need:
- Full CRUD operations
- Automatic URL routing
- Consistent resource management
- Less code for complete functionality