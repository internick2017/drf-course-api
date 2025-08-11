# JWT Authentication Guide

This guide explains how to use JWT (JSON Web Token) authentication in the Django REST Framework API.

## Overview

JWT authentication has been implemented using `djangorestframework-simplejwt`. This provides secure, stateless authentication for your API endpoints.

## JWT Configuration

### Token Settings
- **Access Token Lifetime**: 60 minutes
- **Refresh Token Lifetime**: 1 day
- **Algorithm**: HS256
- **Token Type**: Bearer

### Authentication Classes
The API now uses JWT as the primary authentication method, with fallbacks to session and basic authentication.

## Available Endpoints

### 1. User Registration
**POST** `/api/auth/register/`

Register a new user and receive JWT tokens.

**Request Body:**
```json
{
    "username": "newuser",
    "email": "user@example.com",
    "password": "securepassword123",
    "first_name": "John",
    "last_name": "Doe"
}
```

**Response:**
```json
{
    "message": "User registered successfully",
    "user": {
        "id": 1,
        "username": "newuser",
        "email": "user@example.com",
        "is_staff": false
    },
    "tokens": {
        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
}
```

### 2. User Login
**POST** `/api/auth/login/`

Authenticate user and receive JWT tokens.

**Request Body:**
```json
{
    "username": "newuser",
    "password": "securepassword123"
}
```

**Response:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "message": "Login successful"
}
```

### 3. Token Refresh
**POST** `/api/token/refresh/`

Get a new access token using a refresh token.

**Request Body:**
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### 4. Token Verification
**POST** `/api/token/verify/`

Verify if a token is valid.

**Request Body:**
```json
{
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response:**
```json
{
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

## Using JWT Tokens

### Making Authenticated Requests

Include the access token in the Authorization header:

```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     http://localhost:8000/api/products/
```

### Python Requests Example

```python
import requests

# Login to get tokens
login_data = {
    "username": "your_username",
    "password": "your_password"
}

response = requests.post('http://localhost:8000/api/auth/login/', json=login_data)
tokens = response.json()

# Use access token for authenticated requests
headers = {
    'Authorization': f'Bearer {tokens["access"]}'
}

# Get products (requires authentication)
response = requests.get('http://localhost:8000/api/products/', headers=headers)
products = response.json()

# Create a product (requires admin privileges)
product_data = {
    "name": "New Product",
    "description": "Product description",
    "price": 29.99,
    "stock": 100
}

response = requests.post(
    'http://localhost:8000/api/enhanced/products/',
    json=product_data,
    headers=headers
)
```

### JavaScript/Fetch Example

```javascript
// Login
const loginData = {
    username: 'your_username',
    password: 'your_password'
};

fetch('http://localhost:8000/api/auth/login/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify(loginData)
})
.then(response => response.json())
.then(data => {
    const accessToken = data.access;

    // Use token for authenticated requests
    fetch('http://localhost:8000/api/products/', {
        headers: {
            'Authorization': `Bearer ${accessToken}`
        }
    })
    .then(response => response.json())
    .then(products => console.log(products));
});
```

## Token Management

### Token Expiration
- **Access tokens** expire after 60 minutes
- **Refresh tokens** expire after 1 day
- When an access token expires, use the refresh token to get a new one

### Refreshing Tokens
```python
import requests

refresh_data = {
    "refresh": "your_refresh_token"
}

response = requests.post('http://localhost:8000/api/token/refresh/', json=refresh_data)
new_access_token = response.json()["access"]
```

### Error Handling

Common JWT errors and their meanings:

- **401 Unauthorized**: Invalid or expired access token
- **400 Bad Request**: Invalid refresh token or malformed request
- **500 Internal Server Error**: Server-side authentication error

## Security Best Practices

### 1. Token Storage
- Store tokens securely (not in localStorage for web apps)
- Use secure HTTP-only cookies for web applications
- Implement token rotation for enhanced security

### 2. Token Usage
- Always use HTTPS in production
- Include tokens in Authorization header
- Don't expose tokens in URLs or logs

### 3. Password Security
- Use strong passwords
- Implement password validation
- Consider implementing password reset functionality

## Testing JWT Authentication

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Migrations
```bash
python manage.py migrate
```

### 3. Create a Superuser (Optional)
```bash
python manage.py createsuperuser
```

### 4. Test Authentication Flow

```bash
# 1. Register a new user
curl -X POST http://localhost:8000/api/auth/register/ \
     -H "Content-Type: application/json" \
     -d '{
         "username": "testuser",
         "email": "test@example.com",
         "password": "testpass123",
         "first_name": "Test",
         "last_name": "User"
     }'

# 2. Login to get tokens
curl -X POST http://localhost:8000/api/auth/login/ \
     -H "Content-Type: application/json" \
     -d '{
         "username": "testuser",
         "password": "testpass123"
     }'

# 3. Use access token for authenticated requests
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     http://localhost:8000/api/products/
```

## Integration with Existing Endpoints

All existing API endpoints now support JWT authentication:

- **ViewSet endpoints**: `/api/products/`, `/api/users/`, etc.
- **Generic view endpoints**: `/api/enhanced/products/`, `/api/generic/users/`, etc.
- **Custom endpoints**: `/api/profiling-example/`, `/api/performance-test/`

### Permission Levels

1. **Public endpoints**: No authentication required
2. **Authenticated endpoints**: Valid JWT token required
3. **Admin-only endpoints**: Valid JWT token + admin privileges required

## Troubleshooting

### Common Issues

1. **"Authentication credentials were not provided"**
   - Include the Authorization header with your JWT token

2. **"Token is invalid or expired"**
   - Refresh your access token using the refresh token

3. **"Permission denied"**
   - Check if you have the required permissions (admin for write operations)

### Debug Mode

In development, you can enable debug mode to see detailed error messages:

```python
# In settings.py
DEBUG = True
```

## Production Considerations

1. **Change SECRET_KEY**: Use a strong, unique secret key
2. **HTTPS**: Always use HTTPS in production
3. **Token Lifetime**: Adjust token lifetimes based on security requirements
4. **CORS**: Configure CORS settings for frontend applications
5. **Rate Limiting**: Implement rate limiting for authentication endpoints

## Additional Resources

- [DRF Simple JWT Documentation](https://django-rest-framework-simplejwt.readthedocs.io/)
- [JWT.io](https://jwt.io/) - JWT token decoder and debugger
- [Django REST Framework Authentication](https://www.django-rest-framework.org/api-guide/authentication/)
