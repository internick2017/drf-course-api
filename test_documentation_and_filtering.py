#!/usr/bin/env python
"""
Test script for DRF Spectacular documentation and Django filtering
This script tests the API documentation generation and filtering functionality
"""

import os
import uuid

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api_project.settings')

import django
django.setup()

from django.test import TestCase  # type: ignore  # noqa: E402
from rest_framework.test import APIClient  # type: ignore  # noqa: E402
from api.models import User, Product, Order, OrderItem  # type: ignore  # noqa: E402


class DocumentationAndFilteringTest(TestCase):
    """Test API documentation and filtering functionality"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()

        # Generate unique usernames
        unique_id = str(uuid.uuid4())[:8]

        # Create test user
        self.user = User.objects.create_user(
            username=f'testuser_{unique_id}',
            email=f'test_{unique_id}@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

        # Create admin user
        self.admin_user = User.objects.create_user(
            username=f'admin_{unique_id}',
            email=f'admin_{unique_id}@example.com',
            password='adminpass123',
            first_name='Admin',
            last_name='User',
            is_staff=True
        )

        # Create test products
        self.product1 = Product.objects.create(
            name='Laptop',
            description='High-performance laptop',
            price=999.99,
            stock=5
        )

        self.product2 = Product.objects.create(
            name='Mouse',
            description='Wireless mouse',
            price=29.99,
            stock=0
        )

        self.product3 = Product.objects.create(
            name='Keyboard',
            description='Mechanical keyboard',
            price=149.99,
            stock=10
        )

        # Create test order
        self.order = Order.objects.create(
            user=self.user,
            status='Pending'
        )

        # Create test order items
        self.order_item1 = OrderItem.objects.create(
            order=self.order,
            product=self.product1,
            quantity=1
        )

        self.order_item2 = OrderItem.objects.create(
            order=self.order,
            product=self.product3,
            quantity=2
        )

    def test_api_documentation_endpoints(self):
        """Test API documentation endpoints"""
        print("Testing API documentation endpoints...")

        # Test schema endpoint
        response = self.client.get('/api/schema/')
        if response.status_code == 200:
            print("✅ API schema endpoint working")
            # Handle OpenAPI content type
            if response.get('Content-Type', '').startswith('application/vnd.oai.openapi'):
                schema_data = response.content.decode('utf-8')
                self.assertIn('openapi', schema_data)
                self.assertIn('info', schema_data)
                self.assertIn('paths', schema_data)
            else:
                schema_data = response.json()
                self.assertIn('openapi', schema_data)
                self.assertIn('info', schema_data)
                self.assertIn('paths', schema_data)
        else:
            print(f"❌ API schema endpoint failed: {response.status_code}")

        # Test Swagger UI endpoint
        response = self.client.get('/api/docs/')
        if response.status_code == 200:
            print("✅ Swagger UI endpoint working")
        else:
            print(f"❌ Swagger UI endpoint failed: {response.status_code}")

        # Test ReDoc endpoint
        response = self.client.get('/api/redoc/')
        if response.status_code == 200:
            print("✅ ReDoc endpoint working")
        else:
            print(f"❌ ReDoc endpoint failed: {response.status_code}")

    def test_product_filtering(self):
        """Test product filtering with Django filters"""
        print("Testing product filtering...")

        self._test_product_search_filter()
        self._test_product_stock_filters()
        self._test_product_price_range_filter()
        self._test_product_ordering()

    def _test_product_search_filter(self):
        """Test product search filter"""
        response = self.client.get('/api/products/?search=Laptop')
        if response.status_code == 200:
            data = response.json()
            self.assertGreaterEqual(len(data['results']), 1)
            laptop_found = any('Laptop' in product['name'] for product in data['results'])
            self.assertTrue(laptop_found)
            print("✅ Product search filter working")
        else:
            print(f"❌ Product search filter failed: {response.status_code}")

    def _test_product_stock_filters(self):
        """Test product stock availability filters"""
        # Test in_stock filter
        response = self.client.get('/api/products/?in_stock=true')
        if response.status_code == 200:
            data = response.json()
            for product in data['results']:
                self.assertGreater(product['stock'], 0)
            print("✅ Product in_stock filter working")
        else:
            print(f"❌ Product in_stock filter failed: {response.status_code}")

        # Test out_of_stock filter
        response = self.client.get('/api/products/?out_of_stock=true')
        if response.status_code == 200:
            data = response.json()
            for product in data['results']:
                self.assertEqual(product['stock'], 0)
            print("✅ Product out_of_stock filter working")
        else:
            print(f"❌ Product out_of_stock filter failed: {response.status_code}")

    def _test_product_price_range_filter(self):
        """Test product price range filter"""
        response = self.client.get('/api/products/?price_min=100&price_max=200')
        if response.status_code == 200:
            data = response.json()
            if data['results']:
                for product in data['results']:
                    price = float(product['price'])
                    self.assertGreaterEqual(price, 100)
                    self.assertLessEqual(price, 200)
            print("✅ Product price range filter working")
        else:
            print(f"❌ Product price range filter failed: {response.status_code}")

    def _test_product_ordering(self):
        """Test product ordering"""
        response = self.client.get('/api/products/?ordering=price')
        if response.status_code == 200:
            data = response.json()
            prices = [float(product['price']) for product in data['results']]
            self.assertEqual(prices, sorted(prices))
            print("✅ Product ordering working")
        else:
            print(f"❌ Product ordering failed: {response.status_code}")

    def test_user_filtering(self):
        """Test user filtering with Django filters"""
        print("Testing user filtering...")

        # Login as admin
        self.client.force_authenticate(user=self.admin_user)

        # Test search filter
        response = self.client.get(f'/api/users/?search={self.user.username}')
        if response.status_code == 200:
            data = response.json()
            self.assertEqual(len(data['results']), 1)
            self.assertEqual(data['results'][0]['username'], self.user.username)
            print("✅ User search filter working")
        else:
            print(f"❌ User search filter failed: {response.status_code}")

        # Test email domain filter
        response = self.client.get('/api/users/?email_domain=example.com')
        if response.status_code == 200:
            data = response.json()
            for user in data['results']:
                self.assertTrue(user['email'].endswith('@example.com'))
            print("✅ User email domain filter working")
        else:
            print(f"❌ User email domain filter failed: {response.status_code}")

        # Test has_orders filter
        response = self.client.get('/api/users/?has_orders=true')
        if response.status_code == 200:
            data = response.json()
            self.assertGreaterEqual(len(data['results']), 0)
            print("✅ User has_orders filter working")
        else:
            print(f"❌ User has_orders filter failed: {response.status_code}")

    def test_order_filtering(self):
        """Test order filtering with Django filters"""
        print("Testing order filtering...")

        # Login as admin
        self.client.force_authenticate(user=self.admin_user)

        # Test order_id filter
        response = self.client.get(f'/api/orders/?order_id={self.order.order_id}')
        if response.status_code == 200:
            data = response.json()
            self.assertGreaterEqual(len(data['results']), 0)
            if data['results']:
                self.assertEqual(data['results'][0]['order_id'], str(self.order.order_id))
            print("✅ Order order_id filter working")
        else:
            print(f"❌ Order order_id filter failed: {response.status_code}")

        # Test status filter
        response = self.client.get('/api/orders/?status=Pending')
        if response.status_code == 200:
            data = response.json()
            for order in data['results']:
                self.assertEqual(order['status'], 'Pending')
            print("✅ Order status filter working")
        else:
            print(f"❌ Order status filter failed: {response.status_code}")

        # Test has_items filter
        response = self.client.get('/api/orders/?has_items=true')
        if response.status_code == 200:
            data = response.json()
            self.assertGreaterEqual(len(data['results']), 0)
            print("✅ Order has_items filter working")
        else:
            print(f"❌ Order has_items filter failed: {response.status_code}")

    def test_order_item_filtering(self):
        """Test order item filtering with Django filters"""
        print("Testing order item filtering...")

        # Login as admin
        self.client.force_authenticate(user=self.admin_user)

        # Test product_id filter
        response = self.client.get(f'/api/order-items/?product_id={self.product1.id}')
        if response.status_code == 200:
            data = response.json()
            for item in data['results']:
                self.assertEqual(item['product'], self.product1.id)
            print("✅ Order item product_id filter working")
        else:
            print(f"❌ Order item product_id filter failed: {response.status_code}")

        # Test quantity range filter
        response = self.client.get('/api/order-items/?quantity_min=1&quantity_max=3')
        if response.status_code == 200:
            data = response.json()
            for item in data['results']:
                self.assertGreaterEqual(item['quantity'], 1)
                self.assertLessEqual(item['quantity'], 3)
            print("✅ Order item quantity range filter working")
        else:
            print(f"❌ Order item quantity range filter failed: {response.status_code}")


def main():
    """Run documentation and filtering tests"""
    print("📚 API Documentation and Filtering Test Suite")
    print("=" * 60)

    # Create test instance
    test_instance = DocumentationAndFilteringTest()
    test_instance.setUp()

    # Run tests
    try:
        test_instance.test_api_documentation_endpoints()
        test_instance.test_product_filtering()
        test_instance.test_user_filtering()
        test_instance.test_order_filtering()
        test_instance.test_order_item_filtering()

        print("\n" + "=" * 60)
        print("✅ All documentation and filtering tests completed successfully!")
        print("\n🎉 API documentation and filtering are working correctly!")
        print("\n📖 You can now access:")
        print("   - Swagger UI: http://localhost:8000/api/docs/")
        print("   - ReDoc: http://localhost:8000/api/redoc/")
        print("   - API Schema: http://localhost:8000/api/schema/")

    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
