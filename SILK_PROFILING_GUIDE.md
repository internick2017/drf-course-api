# Django Silk Profiling and Optimization Guide

This guide explains how to use django-silk for profiling and optimizing your Django REST Framework application.

## What is Django Silk?

Django Silk is a profiling tool that helps you identify performance bottlenecks in your Django application by:

- Recording HTTP requests and responses
- Profiling database queries
- Measuring execution time of functions
- Identifying N+1 query problems
- Providing a web interface to analyze performance data

## Installation and Setup

### 1. Installation
```bash
pip install django-silk
```

### 2. Configuration in settings.py

Add to `INSTALLED_APPS`:
```python
INSTALLED_APPS = [
    # ... other apps
    'silk',
]
```

Add to `MIDDLEWARE` (must be first):
```python
MIDDLEWARE = [
    'silk.middleware.SilkyMiddleware',
    # ... other middleware
]
```

### 3. Silk Configuration Settings

```python
# Django Silk Configuration for Profiling
SILKY_PYTHON_PROFILER = True
SILKY_PYTHON_PROFILER_MEMORY = True
SILKY_AUTHENTICATION = True
SILKY_AUTHORISATION = True
SILKY_MAX_RECORDED_REQUESTS = 1000
SILKY_MAX_RECORDED_REQUESTS_CHECK_PERCENT = 10
SILKY_META = True
```

### 4. URL Configuration

Add to your main `urls.py`:
```python
urlpatterns = [
    # ... other URLs
    path('silk/', include('silk.urls', namespace='silk')),
]
```

### 5. Run Migrations
```bash
python manage.py migrate
```

## Usage Examples

### 1. Automatic Profiling

Silk automatically profiles all HTTP requests and database queries. Simply make requests to your API endpoints and check the Silk dashboard at `/silk/`.

### 2. Manual Function Profiling

Use the `@silk_profile` decorator to profile specific functions:

```python
from silk.profiling.profiler import silk_profile

@silk_profile(name='expensive_calculation')
def expensive_calculation(iterations):
    result = 0
    for i in range(iterations):
        result += i * random.random()
    return result
```

### 3. Context Manager Profiling

```python
from silk.profiling.profiler import silk_profile

def some_function():
    with silk_profile(name='my_profile'):
        # Code to profile
        pass
```

## Example Endpoints

This project includes example endpoints to demonstrate Silk profiling:

### 1. Profiling Example
- **URL**: `/api/profiling-example/`
- **Purpose**: Demonstrates different profiling techniques
- **Features**:
  - Manual function profiling
  - Database query profiling
  - Performance timing

### 2. Performance Test
- **URL**: `/api/performance-test/`
- **Purpose**: Compares N+1 vs optimized queries
- **Parameters**:
  - `?test=n_plus_one` - Run N+1 query test
  - `?test=optimized` - Run optimized query test
  - `?test=both` - Run both for comparison

## Silk Dashboard Features

### 1. Requests Overview
- View all recorded HTTP requests
- Filter by method, status code, and time range
- See request/response details

### 2. Database Queries
- Analyze SQL queries executed
- Identify slow queries
- Detect N+1 query problems
- View query execution plans

### 3. Function Profiling
- Profile specific functions with `@silk_profile`
- View execution time and memory usage
- Identify bottlenecks in your code

### 4. Performance Metrics
- Request duration statistics
- Database query count and timing
- Memory usage patterns

## Best Practices for Optimization

### 1. Database Query Optimization

**Problem**: N+1 Query Issue
```python
# Bad - causes N+1 queries
orders = Order.objects.all()
for order in orders:
    print(order.user.email)  # Additional query for each order
```

**Solution**: Use `select_related()` or `prefetch_related()`
```python
# Good - single query with joins
orders = Order.objects.select_related('user').all()
for order in orders:
    print(order.user.email)  # No additional queries
```

### 2. Function Profiling

Profile expensive operations:
```python
@silk_profile(name='data_processing')
def process_large_dataset(data):
    # Your expensive operation here
    pass
```

### 3. Monitoring Production

For production environments:
```python
# Only enable profiling for specific users or conditions
SILKY_AUTHENTICATION = True
SILKY_AUTHORISATION = True

# Limit the number of recorded requests
SILKY_MAX_RECORDED_REQUESTS = 100
```

## Performance Analysis Workflow

1. **Identify Slow Endpoints**: Use Silk dashboard to find slow requests
2. **Analyze Database Queries**: Look for N+1 queries and slow SQL
3. **Profile Functions**: Use `@silk_profile` for specific code sections
4. **Optimize**: Apply database optimizations and code improvements
5. **Measure**: Re-run tests to verify improvements

## Common Performance Issues and Solutions

### 1. N+1 Query Problems
- **Symptoms**: Many similar queries in Silk dashboard
- **Solution**: Use `select_related()` and `prefetch_related()`

### 2. Slow Database Queries
- **Symptoms**: Long execution times in query list
- **Solution**: Add database indexes, optimize queries

### 3. Memory Issues
- **Symptoms**: High memory usage in profiling data
- **Solution**: Optimize data structures, use generators

### 4. Inefficient Serialization
- **Symptoms**: Slow response times despite fast queries
- **Solution**: Optimize serializers, use `SerializerMethodField` wisely

## Security Considerations

1. **Authentication**: Enable `SILKY_AUTHENTICATION = True` in production
2. **Authorization**: Use `SILKY_AUTHORISATION = True` to restrict access
3. **Data Privacy**: Be careful with sensitive data in profiling
4. **Storage**: Regularly clean old profiling data

## Troubleshooting

### Common Issues

1. **Silk not recording requests**:
   - Check middleware order (SilkMiddleware must be first)
   - Verify Silk is in INSTALLED_APPS

2. **Dashboard not accessible**:
   - Check URL configuration
   - Verify authentication settings

3. **Performance impact**:
   - Limit recorded requests in production
   - Use conditional profiling

### Debugging Commands

```bash
# Check Silk tables
python manage.py shell
>>> from silk.models import Request
>>> Request.objects.count()

# Clear old profiling data
python manage.py shell
>>> from silk.models import Request, Response, SQLQuery, Profile
>>> Request.objects.all().delete()
```

## Conclusion

Django Silk is a powerful tool for identifying and fixing performance issues in Django applications. By following this guide and using the example endpoints, you can effectively profile and optimize your Django REST Framework API.

Remember to:
- Use profiling in development and staging environments
- Apply security best practices in production
- Regularly analyze and optimize based on profiling data
- Combine Silk with other monitoring tools for comprehensive performance analysis