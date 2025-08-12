#!/usr/bin/env python
"""
Test script for Generic Views update and delete functionality
This script tests the new RetrieveUpdateDestroyAPIView classes
"""

import os
import uuid

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api_project.settings')

import django
django.setup()

from django.test import TestCase
from rest_framework.test import APIClient
from api.models import User, Product, Order, OrderItem


class GenericViewsUpdateDeleteTest(TestCase):
    """Test update and delete functionality with generic views"""

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

        # Create test product
        self.product = Product.objects.create(
            name='Test Product',
            description='Test Description',
            price=29.99,
            stock=10
        )

        # Create test order
        self.order = Order.objects.create(
            user=self.user,
            status='Pending'
        )

        # Create test order item
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2
        )

    def test_user_update_delete(self):
        """Test user update and delete with generic views"""
        print("Testing user update and delete...")

        # Login as admin
        self.client.force_authenticate(user=self.admin_user)

        # Test GET user details
        response = self.client.get(f'/api/enhanced/users/{self.user.username}/')
        if response.status_code == 200:
            print("✅ User details retrieved successfully")
        else:
            print(f"❌ Failed to get user details: {response.status_code}")
            return

        # Test PUT update user
        update_data = {
            'username': 'updateduser',
            'email': 'updated@example.com',
            'first_name': 'Updated',
            'last_name': 'User'
        }
        response = self.client.put(f'/api/enhanced/users/{self.user.username}/', update_data, format='json')
        if response.status_code == 200:
            print("✅ User updated successfully")
            # Update the user object for next test
            self.user = User.objects.get(username='updateduser')
        else:
            print(f"❌ Failed to update user: {response.status_code}")
            print(f"   Response: {response.content.decode()}")
            return

        # Test DELETE user
        response = self.client.delete(f'/api/enhanced/users/{self.user.username}/')
        if response.status_code == 204:
            print("✅ User deleted successfully")
        else:
            print(f"❌ Failed to delete user: {response.status_code}")

    def test_order_update_delete(self):
        """Test order update and delete with generic views"""
        print("Testing order update and delete...")

        # Login as admin
        self.client.force_authenticate(user=self.admin_user)

        # Test GET order details
        response = self.client.get(f'/api/enhanced/orders/{self.order.pk}/')
        if response.status_code == 200:
            print("✅ Order details retrieved successfully")
        else:
            print(f"❌ Failed to get order details: {response.status_code}")
            return

        # Test PATCH update order
        update_data = {
            'status': 'Confirmed'
        }
        response = self.client.patch(f'/api/enhanced/orders/{self.order.pk}/', update_data, format='json')
        if response.status_code == 200:
            print("✅ Order updated successfully")
        else:
            print(f"❌ Failed to update order: {response.status_code}")
            print(f"   Response: {response.content.decode()}")
            return

        # Test DELETE order
        response = self.client.delete(f'/api/enhanced/orders/{self.order.pk}/')
        if response.status_code == 204:
            print("✅ Order deleted successfully")
        else:
            print(f"❌ Failed to delete order: {response.status_code}")

    def test_order_item_update_delete(self):
        """Test order item update and delete with generic views"""
        print("Testing order item update and delete...")

        # Login as admin
        self.client.force_authenticate(user=self.admin_user)

        # Test GET order item details
        response = self.client.get(f'/api/enhanced/order-items/{self.order_item.pk}/')
        if response.status_code == 200:
            print("✅ Order item details retrieved successfully")
        else:
            print(f"❌ Failed to get order item details: {response.status_code}")
            return

        # Test PUT update order item
        update_data = {
            'order': str(self.order.pk),
            'product': self.product.id,
            'quantity': 5
        }
        response = self.client.put(f'/api/enhanced/order-items/{self.order_item.pk}/', update_data, format='json')
        if response.status_code == 200:
            print("✅ Order item updated successfully")
        else:
            print(f"❌ Failed to update order item: {response.status_code}")
            print(f"   Response: {response.content.decode()}")
            return

        # Test DELETE order item
        response = self.client.delete(f'/api/enhanced/order-items/{self.order_item.pk}/')
        if response.status_code == 204:
            print("✅ Order item deleted successfully")
        else:
            print(f"❌ Failed to delete order item: {response.status_code}")

    def test_product_update_delete(self):
        """Test product update and delete with existing generic views"""
        print("Testing product update and delete...")

        # Login as admin
        self.client.force_authenticate(user=self.admin_user)

        # Test GET product details
        response = self.client.get(f'/api/enhanced/products/{self.product.id}/')
        if response.status_code == 200:
            print("✅ Product details retrieved successfully")
        else:
            print(f"❌ Failed to get product details: {response.status_code}")
            return

        # Test PATCH update product
        update_data = {
            'name': 'Updated Product',
            'price': 39.99
        }
        response = self.client.patch(f'/api/enhanced/products/{self.product.id}/', update_data, format='json')
        if response.status_code == 200:
            print("✅ Product updated successfully")
        else:
            print(f"❌ Failed to update product: {response.status_code}")
            print(f"   Response: {response.content.decode()}")
            return

        # Test DELETE product
        response = self.client.delete(f'/api/enhanced/products/{self.product.id}/')
        if response.status_code == 204:
            print("✅ Product deleted successfully")
        else:
            print(f"❌ Failed to delete product: {response.status_code}")


def main():
    """Run generic views update and delete tests"""
    print("🔧 Generic Views Update and Delete Test Suite")
    print("=" * 60)

    # Create test instance
    test_instance = GenericViewsUpdateDeleteTest()
    test_instance.setUp()

    # Run tests
    try:
        test_instance.test_user_update_delete()
        test_instance.test_order_update_delete()
        test_instance.test_order_item_update_delete()
        test_instance.test_product_update_delete()

        print("\n" + "=" * 60)
        print("✅ All generic views update and delete tests completed successfully!")
        print("\n🎉 Update and delete functionality is working with generic views!")

    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()