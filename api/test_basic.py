from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
import uuid

from .models import Product, Order, OrderItem
from .serializers import ProductSerializer, OrderSerializer, OrderItemSerializer

User = get_user_model()


class BasicModelTests(TestCase):
    """Basic test cases for models"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.product = Product.objects.create(
            name='Test Product',
            description='Test Description',
            price=Decimal('99.99'),
            stock=10
        )

    def test_product_creation(self):
        """Test product creation and properties"""
        self.assertEqual(self.product.name, 'Test Product')
        self.assertEqual(self.product.price, Decimal('99.99'))
        self.assertEqual(self.product.stock, 10)
        self.assertTrue(self.product.in_stock)
        self.assertEqual(str(self.product), 'Test Product')

    def test_product_out_of_stock(self):
        """Test product out of stock property"""
        self.product.stock = 0
        self.product.save()
        self.assertFalse(self.product.in_stock)

    def test_order_creation(self):
        """Test order creation"""
        order = Order.objects.create(
            user=self.user,
            status='Pending'
        )
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.status, 'Pending')
        self.assertIsInstance(order.order_id, uuid.UUID)
        self.assertEqual(str(order), f'Order {order.order_id} by {self.user.username}')

    def test_order_item_creation(self):
        """Test order item creation and properties"""
        order = Order.objects.create(user=self.user)
        order_item = OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=2
        )
        self.assertEqual(order_item.quantity, 2)
        self.assertEqual(order_item.item_subtotal, Decimal('199.98'))
        self.assertEqual(str(order_item), f'2 x {self.product.name} in Order {order.order_id}')


class BasicSerializerTests(TestCase):
    """Basic test cases for serializers"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.product = Product.objects.create(
            name='Test Product',
            description='Test Description',
            price=Decimal('99.99'),
            stock=10
        )

    def test_product_serializer(self):
        """Test product serializer"""
        serializer = ProductSerializer(self.product)
        data = serializer.data

        self.assertEqual(data['name'], 'Test Product')
        self.assertEqual(data['price'], '99.99')
        self.assertEqual(data['stock'], 10)
        self.assertTrue(data['in_stock'])

    def test_product_serializer_validation(self):
        """Test product serializer validation"""
        # Test valid data
        valid_data = {
            'name': 'Valid Product',
            'description': 'Valid Description',
            'price': '50.00',
            'stock': 5
        }
        serializer = ProductSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())

        # Test invalid price
        invalid_data = {
            'name': 'Invalid Product',
            'description': 'Invalid Description',
            'price': '-10.00',
            'stock': 5
        }
        serializer = ProductSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('price', serializer.errors)

    def test_order_serializer(self):
        """Test order serializer"""
        order = Order.objects.create(user=self.user)
        order_item = OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=2
        )

        serializer = OrderSerializer(order)
        data = serializer.data

        self.assertEqual(data['user'], self.user.id)
        self.assertEqual(data['status'], 'Pending')
        self.assertEqual(len(data['items']), 1)
        self.assertEqual(data['total_price'], '199.98')

    def test_order_item_serializer(self):
        """Test order item serializer"""
        order = Order.objects.create(user=self.user)
        order_item = OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=3
        )

        serializer = OrderItemSerializer(order_item)
        data = serializer.data

        self.assertEqual(data['product_name'], 'Test Product')
        self.assertEqual(data['product_price'], '99.99')
        self.assertEqual(data['quantity'], 3)
        self.assertEqual(data['item_subtotal'], '299.97')


class BasicPermissionTests(APITestCase):
    """Basic test cases for permissions"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )

        self.product = Product.objects.create(
            name='Test Product',
            description='Test Description',
            price=Decimal('99.99'),
            stock=10
        )

    def test_product_read_permission_anonymous(self):
        """Test that anonymous users can read products"""
        url = reverse('product-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_product_write_permission_authenticated(self):
        """Test that authenticated users can create products"""
        self.client.force_authenticate(user=self.user)
        url = reverse('product-list')
        data = {
            'name': 'New Product',
            'description': 'New Description',
            'price': '50.00',
            'stock': 5
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_product_write_permission_anonymous(self):
        """Test that anonymous users cannot create products"""
        url = reverse('product-list')
        data = {
            'name': 'New Product',
            'description': 'New Description',
            'price': '50.00',
            'stock': 5
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_access_permission_admin(self):
        """Test that admins can access user list"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_access_permission_non_admin(self):
        """Test that non-admins cannot access user list"""
        self.client.force_authenticate(user=self.user)
        url = reverse('user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class BasicViewTests(APITestCase):
    """Basic test cases for views"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.product = Product.objects.create(
            name='Test Product',
            description='Test Description',
            price=Decimal('99.99'),
            stock=10
        )

    def test_product_list_view(self):
        """Test product list view"""
        url = reverse('product-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_product_detail_view(self):
        """Test product detail view"""
        url = reverse('product-detail', kwargs={'pk': self.product.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Product')

    def test_product_create_view(self):
        """Test product create view"""
        self.client.force_authenticate(user=self.user)
        url = reverse('product-list')
        data = {
            'name': 'New Product',
            'description': 'New Description',
            'price': '75.00',
            'stock': 15
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 2)

    def test_product_update_view(self):
        """Test product update view"""
        self.client.force_authenticate(user=self.user)
        url = reverse('product-detail', kwargs={'pk': self.product.id})
        data = {
            'name': 'Updated Product',
            'description': 'Updated Description',
            'price': '1099.99',
            'stock': 8
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Updated Product')

    def test_product_delete_view(self):
        """Test product delete view"""
        self.client.force_authenticate(user=self.user)
        url = reverse('product-detail', kwargs={'pk': self.product.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Product.objects.count(), 0)


class BasicOrderTests(APITestCase):
    """Basic test cases for order functionality"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.product = Product.objects.create(
            name='Test Product',
            description='Test Description',
            price=Decimal('99.99'),
            stock=10
        )

    def test_order_creation(self):
        """Test order creation"""
        self.client.force_authenticate(user=self.user)
        url = reverse('order-list')
        data = {
            'status': 'Pending'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.filter(user=self.user).count(), 1)

    def test_order_list_user_specific(self):
        """Test that users only see their own orders"""
        # Create an order for the user
        order = Order.objects.create(user=self.user, status='Pending')

        self.client.force_authenticate(user=self.user)
        url = reverse('order-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only user's order

    def test_order_statistics(self):
        """Test order statistics endpoint"""
        # Create some orders for the user
        Order.objects.create(user=self.user, status='Pending')
        Order.objects.create(user=self.user, status='Confirmed')

        self.client.force_authenticate(user=self.user)
        url = reverse('order-statistics')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        self.assertEqual(data['total_orders'], 2)
        self.assertEqual(data['pending_orders'], 1)
        self.assertEqual(data['confirmed_orders'], 1)
        self.assertEqual(data['cancelled_orders'], 0)


class BasicProductInfoTests(APITestCase):
    """Basic test cases for product info endpoint"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()

        # Create test products
        self.product1 = Product.objects.create(
            name='Laptop',
            description='Gaming laptop',
            price=Decimal('999.99'),
            stock=5
        )
        self.product2 = Product.objects.create(
            name='Mouse',
            description='Wireless mouse',
            price=Decimal('29.99'),
            stock=0
        )

    def test_product_info_basic(self):
        """Test basic product info endpoint"""
        url = reverse('product-info')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['in_stock_count'], 1)
        self.assertEqual(data['out_of_stock_count'], 1)
        self.assertEqual(data['max_price'], 999.99)
        self.assertEqual(data['min_price'], 29.99)


class BasicAPIIntegrationTests(APITestCase):
    """Basic integration tests for the complete API workflow"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.product = Product.objects.create(
            name='Test Product',
            description='Test Description',
            price=Decimal('99.99'),
            stock=10
        )

    def test_complete_workflow(self):
        """Test complete API workflow: create order, add items, update status"""
        self.client.force_authenticate(user=self.user)

        # 1. Create an order
        order_url = reverse('order-list')
        order_data = {'status': 'Pending'}
        response = self.client.post(order_url, order_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order_id = response.data['order_id']

        # 2. Create order item
        order_item_url = reverse('orderitem-list')
        order_item_data = {
            'order': order_id,
            'product': self.product.id,
            'quantity': 2
        }
        response = self.client.post(order_item_url, order_item_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 3. Update order status
        order_detail_url = reverse('order-detail', kwargs={'pk': order_id})
        update_data = {'status': 'Confirmed'}
        response = self.client.patch(order_detail_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 4. Verify order details
        response = self.client.get(order_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'Confirmed')
        self.assertEqual(len(response.data['items']), 1)
        self.assertEqual(response.data['total_price'], '199.98')

    def test_error_handling(self):
        """Test error handling in the API"""
        self.client.force_authenticate(user=self.user)

        # Test invalid product creation
        product_url = reverse('product-list')
        invalid_data = {
            'name': 'Invalid Product',
            'price': '-10.00',  # Invalid negative price
            'stock': -5  # Invalid negative stock
        }
        response = self.client.post(product_url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('price', response.data)
        self.assertIn('stock', response.data)
