# Django REST Framework E-commerce API

A Django REST Framework API project for an e-commerce system with user management, products, orders, and order items.

## Features

- Django 5.0+ with Django REST Framework
- Custom User model extending AbstractUser
- Product management with stock tracking
- Order system with status management
- Order items with quantity and subtotal calculation
- Image upload support for products
- Admin interface for data management
- JSON API responses
- Authentication and permissions setup

## Models

### User
- Custom user model extending Django's AbstractUser
- Username, email, first_name, last_name, etc.

### Product
- Name, description, price, stock
- Image upload support
- `in_stock` property for stock availability

### Order
- UUID-based order ID
- User relationship
- Status choices (Pending, Confirmed, Cancelled)
- Many-to-many relationship with products through OrderItem

### OrderItem
- Links orders and products
- Quantity tracking
- `item_subtotal` property for price calculation

## Setup

1. **Activate virtual environment:**
   ```bash
   venv/Scripts/activate  # Windows
   # or
   source venv/bin/activate  # Linux/Mac
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

4. **Create superuser (optional):**
   ```bash
   python manage.py createsuperuser
   ```

5. **Run development server:**
   ```bash
   python manage.py runserver
   ```

## API Endpoints

- **Admin Interface:** `http://localhost:8000/admin/`
- **API Root:** `http://localhost:8000/api/`
- **Users API:** `http://localhost:8000/api/users/`
- **Products API:** `http://localhost:8000/api/products/`
- **Orders API:** `http://localhost:8000/api/orders/`
- **Order Items API:** `http://localhost:8000/api/order-items/`
- **API Auth:** `http://localhost:8000/api-auth/`

## API Usage

### Users Endpoints
- `GET /api/users/` - List all users (admin only)
- `POST /api/users/` - Create a new user
- `GET /api/users/{id}/` - Retrieve a specific user
- `PUT /api/users/{id}/` - Update a specific user
- `DELETE /api/users/{id}/` - Delete a specific user

### Products Endpoints
- `GET /api/products/` - List all products
- `POST /api/products/` - Create a new product (authenticated)
- `GET /api/products/{id}/` - Retrieve a specific product
- `PUT /api/products/{id}/` - Update a specific product (authenticated)
- `DELETE /api/products/{id}/` - Delete a specific product (authenticated)
- `GET /api/products/{id}/in_stock/` - Check if product is in stock

### Orders Endpoints
- `GET /api/orders/` - List user's orders (authenticated)
- `POST /api/orders/` - Create a new order (authenticated)
- `GET /api/orders/{order_id}/` - Retrieve a specific order
- `PUT /api/orders/{order_id}/` - Update a specific order
- `DELETE /api/orders/{order_id}/` - Delete a specific order

### Order Items Endpoints
- `GET /api/order-items/` - List all order items (authenticated)
- `POST /api/order-items/` - Create a new order item (authenticated)
- `GET /api/order-items/{id}/` - Retrieve a specific order item
- `PUT /api/order-items/{id}/` - Update a specific order item
- `DELETE /api/order-items/{id}/` - Delete a specific order item

### Example JSON Data

#### Product
```json
{
    "name": "Example Product",
    "description": "This is an example product",
    "price": "29.99",
    "stock": 100
}
```

#### Order
```json
{
    "user": 1,
    "status": "Pending"
}
```

#### Order Item
```json
{
    "order": "uuid-here",
    "product": 1,
    "quantity": 2
}
```

## Project Structure

```
drf-course-api/
├── api_project/          # Main Django project
│   ├── settings.py       # Django settings
│   ├── urls.py          # Main URL configuration
│   └── wsgi.py          # WSGI configuration
├── api/                  # API app
│   ├── models.py        # Database models (User, Product, Order, OrderItem)
│   ├── serializers.py   # DRF serializers
│   ├── views.py         # API views and ViewSets
│   ├── urls.py          # API URL patterns
│   └── admin.py         # Admin interface configuration
├── media/               # User uploaded files (product images)
├── requirements.txt      # Python dependencies
├── manage.py            # Django management script
└── README.md           # This file
```

## Authentication

The API uses Django REST Framework's built-in authentication:
- Session Authentication (for web interface)
- Basic Authentication (for API clients)

### Permissions
- **Users:** Full access for authenticated users
- **Products:** Read access for all, write access for authenticated users
- **Orders:** Users can only access their own orders
- **Order Items:** Full access for authenticated users

## Media Files

Product images are stored in the `media/products/` directory and served at `/media/products/` URLs.

## Development

To add new models and endpoints:

1. Create models in `api/models.py`
2. Create serializers in `api/serializers.py`
3. Create views in `api/views.py`
4. Add URL patterns in `api/urls.py`
5. Register models in `api/admin.py`
6. Run `python manage.py makemigrations`
7. Run `python manage.py migrate`