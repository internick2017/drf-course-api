#!/usr/bin/env python3
"""
Test script for Django REST Framework Generic Views
Demonstrates ListAPIView and RetrieveAPIView functionality

Usage:
    python test_generic_views.py
"""

import requests
import json
from urllib.parse import urlencode

# Base URL for the API
BASE_URL = "http://localhost:8000/api"

def print_response(response, title):
    """Print formatted API response"""
    print(f"\n{'='*50}")
    print(f"{title}")
    print(f"{'='*50}")
    print(f"Status Code: {response.status_code}")
    print(f"URL: {response.url}")

    if response.status_code == 200:
        try:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
        except json.JSONDecodeError:
            print(f"Response: {response.text}")
    else:
        print(f"Error: {response.text}")
    print(f"{'='*50}")

def test_list_api_view():
    """Test ListAPIView functionality"""
    print("\n🧪 Testing ListAPIView Examples")

    # Test 1: Get all products
    response = requests.get(f"{BASE_URL}/generic/products/")
    print_response(response, "1. Get All Products (ListAPIView)")

    # Test 2: Filter products in stock
    params = {'in_stock': 'true'}
    response = requests.get(f"{BASE_URL}/generic/products/?{urlencode(params)}")
    print_response(response, "2. Filter Products In Stock")

    # Test 3: Filter products by price range
    params = {'min_price': '10', 'max_price': '100'}
    response = requests.get(f"{BASE_URL}/generic/products/?{urlencode(params)}")
    print_response(response, "3. Filter Products by Price Range")

    # Test 4: Get all users (requires authentication)
    response = requests.get(f"{BASE_URL}/generic/users/")
    print_response(response, "4. Get All Users (Requires Authentication)")

    # Test 5: Filter users by username
    params = {'username': 'admin'}
    response = requests.get(f"{BASE_URL}/generic/users/?{urlencode(params)}")
    print_response(response, "5. Filter Users by Username")

def test_retrieve_api_view():
    """Test RetrieveAPIView functionality"""
    print("\n🔍 Testing RetrieveAPIView Examples")

    # Test 1: Get specific product by ID
    response = requests.get(f"{BASE_URL}/generic/products/1/")
    print_response(response, "1. Get Product by ID (RetrieveAPIView)")

    # Test 2: Get non-existent product (should return 404)
    response = requests.get(f"{BASE_URL}/generic/products/999/")
    print_response(response, "2. Get Non-existent Product (404 Test)")

    # Test 3: Get user by username (requires authentication)
    response = requests.get(f"{BASE_URL}/generic/users/admin/")
    print_response(response, "3. Get User by Username (Requires Authentication)")

def test_comparison_with_viewsets():
    """Compare generic views with ViewSets"""
    print("\n⚖️ Comparing Generic Views vs ViewSets")

    # Test ViewSet endpoint (full CRUD)
    response = requests.get(f"{BASE_URL}/products/")
    print_response(response, "ViewSet: GET /products/ (Full CRUD available)")

    # Test Generic View endpoint (read-only)
    response = requests.get(f"{BASE_URL}/generic/products/")
    print_response(response, "Generic View: GET /generic/products/ (Read-only)")

def test_advanced_filtering():
    """Test advanced filtering capabilities"""
    print("\n🎯 Testing Advanced Filtering")

    # Test multiple filters combined
    params = {
        'in_stock': 'true',
        'min_price': '5',
        'max_price': '50'
    }
    response = requests.get(f"{BASE_URL}/generic/products/?{urlencode(params)}")
    print_response(response, "Combined Filters: In Stock + Price Range")

def main():
    """Main test function"""
    print("🚀 Django REST Framework Generic Views Test")
    print("Make sure your Django server is running on http://localhost:8000")

    try:
        # Test ListAPIView
        test_list_api_view()

        # Test RetrieveAPIView
        test_retrieve_api_view()

        # Test comparison
        test_comparison_with_viewsets()

        # Test advanced filtering
        test_advanced_filtering()

        print("\n✅ All tests completed!")
        print("\n📝 Notes:")
        print("- Some endpoints require authentication")
        print("- 404 responses are expected for non-existent resources")
        print("- Check the Django server console for custom logging")

    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to Django server")
        print("Make sure to run: python manage.py runserver")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()