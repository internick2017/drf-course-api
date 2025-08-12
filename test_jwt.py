#!/usr/bin/env python
"""
Test script for JWT authentication functionality
This script tests the JWT authentication setup without running the server
"""

import os
import django
from django.test import TestCase
from rest_framework.test import APIClient
from api.models import User
import uuid


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api_project.settings')
django.setup()


class JWTAuthenticationTest(TestCase):
    """Test JWT authentication functionality"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        # Generate unique username for each test
        unique_id = str(uuid.uuid4())[:8]
        self.user_data = {
            'username': f'testuser_{unique_id}',
            'email': f'test_{unique_id}@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }

    def test_user_registration(self):
        """Test user registration with JWT token response"""
        print("Testing user registration...")

        response = self.client.post('/api/auth/register/', self.user_data, format='json')

        if response.status_code == 201:
            print("✅ User registration successful")
            data = response.json()
            self.assertIn('tokens', data)
            self.assertIn('access', data['tokens'])
            self.assertIn('refresh', data['tokens'])
            self.assertIn('user', data)
            print(f"   User ID: {data['user']['id']}")
            print(f"   Username: {data['user']['username']}")
            return data['tokens']['access']
        else:
            print(f"❌ User registration failed: {response.status_code}")
            print(f"   Response: {response.content.decode()}")
            return None

    def test_user_login(self):
        """Test user login with JWT token response"""
        print("Testing user login...")

        # First create a user
        User.objects.create_user(
            username=self.user_data['username'],
            email=self.user_data['email'],
            password=self.user_data['password'],
            first_name=self.user_data['first_name'],
            last_name=self.user_data['last_name']
        )

        login_data = {
            'username': self.user_data['username'],
            'password': self.user_data['password']
        }

        response = self.client.post('/api/auth/login/', login_data, format='json')

        if response.status_code == 200:
            print("✅ User login successful")
            data = response.json()
            self.assertIn('access', data)
            self.assertIn('refresh', data)
            self.assertIn('message', data)
            print(f"   Access token: {data['access'][:50]}...")
            return data['access']
        else:
            print(f"❌ User login failed: {response.status_code}")
            print(f"   Response: {response.content.decode()}")
            return None

    def test_authenticated_request(self):
        """Test making authenticated requests with JWT token"""
        print("Testing authenticated requests...")

        # Create a user and get token
        User.objects.create_user(
            username=self.user_data['username'],
            email=self.user_data['email'],
            password=self.user_data['password']
        )

        login_data = {
            'username': self.user_data['username'],
            'password': self.user_data['password']
        }

        response = self.client.post('/api/auth/login/', login_data, format='json')
        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code}")
            return

        token = response.json()['access']

        # Test authenticated request
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/products/')

        if response.status_code == 200:
            print("✅ Authenticated request successful")
        else:
            print(f"❌ Authenticated request failed: {response.status_code}")
            print(f"   Response: {response.content.decode()}")

    def test_token_refresh(self):
        """Test token refresh functionality"""
        print("Testing token refresh...")

        # Create a user and get tokens
        User.objects.create_user(
            username=self.user_data['username'],
            email=self.user_data['email'],
            password=self.user_data['password']
        )

        login_data = {
            'username': self.user_data['username'],
            'password': self.user_data['password']
        }

        response = self.client.post('/api/auth/login/', login_data, format='json')
        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code}")
            return

        tokens = response.json()
        refresh_token = tokens['refresh']

        # Test token refresh
        refresh_data = {'refresh': refresh_token}
        response = self.client.post('/api/token/refresh/', refresh_data, format='json')

        if response.status_code == 200:
            print("✅ Token refresh successful")
            data = response.json()
            self.assertIn('access', data)
            print(f"   New access token: {data['access'][:50]}...")
        else:
            print(f"❌ Token refresh failed: {response.status_code}")
            print(f"   Response: {response.content.decode()}")


def main():
    """Run JWT authentication tests"""
    print("🔐 JWT Authentication Test Suite")
    print("=" * 50)

    # Create test instance
    test_instance = JWTAuthenticationTest()
    test_instance.setUp()

    # Run tests
    try:
        test_instance.test_user_registration()
        test_instance.test_user_login()
        test_instance.test_authenticated_request()
        test_instance.test_token_refresh()

        print("\n" + "=" * 50)
        print("✅ All JWT authentication tests completed successfully!")
        print("\n🎉 JWT authentication is properly configured and working!")

    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
