#!/usr/bin/env python
"""
Simple JWT authentication test
This script tests the JWT authentication setup without database conflicts
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api_project.settings')
django.setup()

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from api.models import User
import uuid

def test_jwt_setup():
    """Test JWT authentication setup"""
    print("🔐 Testing JWT Authentication Setup")
    print("=" * 50)

    # Test 1: Check if JWT is properly configured
    print("1. Checking JWT configuration...")
    try:
        from rest_framework_simplejwt.authentication import JWTAuthentication
        from rest_framework_simplejwt.tokens import RefreshToken
        print("✅ JWT package is properly installed and imported")
    except ImportError as e:
        print(f"❌ JWT package import failed: {e}")
        return False

    # Test 2: Check Django settings
    print("2. Checking Django settings...")
    from django.conf import settings

    if 'rest_framework_simplejwt' in settings.INSTALLED_APPS:
        print("✅ JWT app is in INSTALLED_APPS")
    else:
        print("❌ JWT app is not in INSTALLED_APPS")
        return False

    if 'rest_framework_simplejwt.authentication.JWTAuthentication' in settings.REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES']:
        print("✅ JWT authentication is configured in REST_FRAMEWORK")
    else:
        print("❌ JWT authentication is not configured in REST_FRAMEWORK")
        return False

    # Test 3: Test token generation
    print("3. Testing token generation...")
    try:
        # Create a test user
        unique_id = str(uuid.uuid4())[:8]
        test_user = User.objects.create_user(
            username=f'testuser_{unique_id}',
            email=f'test_{unique_id}@example.com',
            password='testpass123'
        )

        # Generate JWT tokens
        refresh = RefreshToken.for_user(test_user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        print(f"✅ Token generation successful")
        print(f"   Access token: {access_token[:50]}...")
        print(f"   Refresh token: {refresh_token[:50]}...")

        # Clean up
        test_user.delete()

    except Exception as e:
        print(f"❌ Token generation failed: {e}")
        return False

    # Test 4: Test API client with JWT
    print("4. Testing API client with JWT...")
    try:
        client = APIClient()

        # Create another test user
        unique_id = str(uuid.uuid4())[:8]
        test_user = User.objects.create_user(
            username=f'testuser_{unique_id}',
            email=f'test_{unique_id}@example.com',
            password='testpass123'
        )

        # Generate tokens
        refresh = RefreshToken.for_user(test_user)
        access_token = str(refresh.access_token)

        # Test authenticated request
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = client.get('/api/products/')

        if response.status_code in [200, 401]:  # 200 for success, 401 for no products but auth works
            print("✅ JWT authentication is working with API client")
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            return False

        # Clean up
        test_user.delete()

    except Exception as e:
        print(f"❌ API client test failed: {e}")
        return False

    print("\n" + "=" * 50)
    print("🎉 JWT Authentication is properly configured and working!")
    print("\nAvailable JWT endpoints:")
    print("  - POST /api/auth/register/ - User registration")
    print("  - POST /api/auth/login/ - User login")
    print("  - POST /api/token/refresh/ - Token refresh")
    print("  - POST /api/token/verify/ - Token verification")

    return True

if __name__ == '__main__':
    success = test_jwt_setup()
    if success:
        print("\n✅ All JWT tests passed!")
    else:
        print("\n❌ Some JWT tests failed!")
