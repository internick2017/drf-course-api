# Dynamic Filtering Guide

This guide explains the comprehensive dynamic filtering capabilities implemented in your Django REST Framework project.

## Overview

All views and ViewSets now support advanced dynamic filtering through query parameters, making your API highly flexible and powerful for frontend applications.

## Product Filtering

### Endpoints
- `GET /api/products/` (ViewSet)
- `GET /api/generic/products/` (Generic View)

### Available Filters

#### Search
```http
GET /api/products/?search=laptop
```
Searches in product name and description (case-insensitive).

#### Stock Availability
```http
GET /api/products/?in_stock=true
GET /api/products/?in_stock=false
```

#### Price Range
```http
GET /api/products/?min_price=100&max_price=500
GET /api/products/?min_price=50
GET /api/products/?max_price=1000
```

#### Stock Range
```http
GET /api/products/?min_stock=10&max_stock=100
GET /api/products/?min_stock=5
GET /api/products/?max_stock=50
```

#### Ordering
```http
GET /api/products/?ordering=name
GET /api/products/?ordering=-price
GET /api/products/?ordering=stock
GET /api/products/?ordering=-id
```

#### Limit Results
```http
GET /api/products/?limit=10
```

#### Combined Filters
```http
GET /api/products/?search=laptop&in_stock=true&min_price=100&max_price=500&ordering=-price&limit=5
```

## User Filtering

### Endpoints
- `GET /api/users/` (ViewSet)
- `GET /api/generic/users/` (Generic View)

### Available Filters

#### Search
```http
GET /api/users/?search=john
```
Searches in username, first_name, last_name, and email.

#### Username Match
```http
GET /api/users/?username=john
```

#### Email Domain
```http
GET /api/users/?email_domain=gmail.com
```

#### Active Status
```http
GET /api/users/?is_active=true
GET /api/users/?is_active=false
```

#### Date Range (Date Joined)
```http
GET /api/users/?date_joined_after=2024-01-01
GET /api/users/?date_joined_before=2024-12-31
GET /api/users/?date_joined_after=2024-01-01&date_joined_before=2024-06-30
```

#### Ordering
```http
GET /api/users/?ordering=username
GET /api/users/?ordering=-date_joined
GET /api/users/?ordering=email
GET /api/users/?ordering=-first_name
```

#### Limit Results
```http
GET /api/users/?limit=20
```

## Order Filtering

### Endpoints
- `GET /api/orders/` (ViewSet)
- `GET /api/generic/orders/` (Generic View)

### Available Filters

#### Status
```http
GET /api/orders/?status=Pending
GET /api/orders/?status=Confirmed
GET /api/orders/?status=Cancelled
```

#### Date Range (Created)
```http
GET /api/orders/?created_after=2024-01-01
GET /api/orders/?created_before=2024-12-31
GET /api/orders/?created_after=2024-01-01&created_before=2024-06-30
```

#### Has Items
```http
GET /api/orders/?has_items=true
GET /api/orders/?has_items=false
```

#### Ordering
```http
GET /api/orders/?ordering=created_at
GET /api/orders/?ordering=-created_at
GET /api/orders/?ordering=status
GET /api/orders/?ordering=-order_id
```

#### Limit Results
```http
GET /api/orders/?limit=10
```

### Order Statistics
```http
GET /api/orders/statistics/
```
Returns:
```json
{
    "total_orders": 15,
    "pending_orders": 3,
    "confirmed_orders": 10,
    "cancelled_orders": 2,
    "orders_with_items": 12,
    "orders_without_items": 3
}
```

## OrderItem Filtering

### Endpoints
- `GET /api/order-items/` (ViewSet)

### Available Filters

#### Filter by Order
```http
GET /api/order-items/?order_id=uuid-here
```

#### Filter by Product
```http
GET /api/order-items/?product_id=1
```

#### Quantity Range
```http
GET /api/order-items/?min_quantity=5
GET /api/order-items/?max_quantity=10
GET /api/order-items/?min_quantity=1&max_quantity=20
```

#### Subtotal Range
```http
GET /api/order-items/?min_subtotal=50
GET /api/order-items/?max_subtotal=200
GET /api/order-items/?min_subtotal=25&max_subtotal=150
```

#### Ordering
```http
GET /api/order-items/?ordering=quantity
GET /api/order-items/?ordering=-quantity
GET /api/order-items/?ordering=product__name
GET /api/order-items/?ordering=-order__created_at
```

## Product Information with Filtering

### Endpoint
- `GET /api/products/info/`

### Available Filters
All product filters work with the info endpoint:

```http
GET /api/products/info/?search=laptop&in_stock=true&min_price=100
```

Returns filtered statistics:
```json
{
    "products": [...],
    "count": 5,
    "max_price": 1500.00,
    "min_price": 100.00,
    "average_price": 750.00,
    "in_stock_count": 5,
    "out_of_stock_count": 0,
    "total_stock": 150,
    "average_stock": 30.0,
    "filters_applied": {
        "search": "laptop",
        "in_stock": "true",
        "min_price": "100",
        "max_price": null
    }
}
```

## Advanced Usage Examples

### Complex Product Search
```http
GET /api/products/?search=gaming&in_stock=true&min_price=500&max_price=2000&min_stock=5&ordering=-price&limit=10
```

### User Analytics
```http
GET /api/users/?is_active=true&date_joined_after=2024-01-01&ordering=-date_joined&limit=50
```

### Order Analysis
```http
GET /api/orders/?status=Confirmed&created_after=2024-01-01&has_items=true&ordering=-created_at
```

### OrderItem Analysis
```http
GET /api/order-items/?min_quantity=2&min_subtotal=100&ordering=-quantity
```

## Security Features

### Input Validation
- All numeric inputs are validated with try-catch blocks
- Invalid values are ignored rather than causing errors
- Date parsing is safe and handles invalid formats

### SQL Injection Prevention
- All filtering uses Django ORM (parameterized queries)
- Ordering fields are validated against allowed lists
- No raw SQL queries are used

### Access Control
- Order filtering is user-specific (users can only see their own orders)
- Proper permission classes are maintained
- Authentication is required for sensitive endpoints

## Performance Optimizations

### Database Queries
- Uses `select_related()` and `prefetch_related()` for efficient queries
- Avoids N+1 query problems
- Optimized for common filtering patterns

### Caching Considerations
- Filter results can be cached based on query parameters
- Consider implementing Redis caching for frequently used filters

## Frontend Integration

### JavaScript Example
```javascript
// Build filter URL
function buildFilterUrl(filters) {
    const params = new URLSearchParams();

    if (filters.search) params.append('search', filters.search);
    if (filters.inStock !== undefined) params.append('in_stock', filters.inStock);
    if (filters.minPrice) params.append('min_price', filters.minPrice);
    if (filters.maxPrice) params.append('max_price', filters.maxPrice);
    if (filters.ordering) params.append('ordering', filters.ordering);
    if (filters.limit) params.append('limit', filters.limit);

    return `/api/products/?${params.toString()}`;
}

// Usage
const filters = {
    search: 'laptop',
    inStock: true,
    minPrice: 100,
    maxPrice: 1000,
    ordering: '-price',
    limit: 10
};

const url = buildFilterUrl(filters);
fetch(url)
    .then(response => response.json())
    .then(data => console.log(data));
```

### React Example
```jsx
import { useState, useEffect } from 'react';

function ProductList() {
    const [products, setProducts] = useState([]);
    const [filters, setFilters] = useState({
        search: '',
        inStock: true,
        minPrice: '',
        maxPrice: '',
        ordering: 'name'
    });

    useEffect(() => {
        const params = new URLSearchParams();
        Object.entries(filters).forEach(([key, value]) => {
            if (value !== '' && value !== null) {
                params.append(key, value);
            }
        });

        fetch(`/api/products/?${params.toString()}`)
            .then(response => response.json())
            .then(data => setProducts(data));
    }, [filters]);

    return (
        <div>
            {/* Filter controls */}
            <input
                type="text"
                placeholder="Search products..."
                value={filters.search}
                onChange={(e) => setFilters({...filters, search: e.target.value})}
            />
            {/* More filter controls */}

            {/* Product list */}
            {products.map(product => (
                <div key={product.id}>{product.name}</div>
            ))}
        </div>
    );
}
```

## Best Practices

1. **Use Appropriate Filters**: Choose filters that match your use case
2. **Combine Filters**: Use multiple filters together for precise results
3. **Order Results**: Always specify ordering for consistent results
4. **Limit Results**: Use limit parameter to control response size
5. **Cache Results**: Implement caching for frequently used filter combinations
6. **Validate Inputs**: Always validate filter parameters on the frontend
7. **Handle Errors**: Implement proper error handling for invalid filters

## Future Enhancements

- **Full-text Search**: Implement PostgreSQL full-text search
- **Geolocation Filtering**: Add location-based filtering
- **Faceted Search**: Add category and tag-based filtering
- **Elasticsearch Integration**: For advanced search capabilities
- **Filter Presets**: Save and reuse common filter combinations
