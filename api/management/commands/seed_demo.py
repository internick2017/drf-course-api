from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from api.models import Product, Order, OrderItem
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed demo data for portfolio showcase'

    def handle(self, *args, **kwargs):
        # Demo user
        demo, created = User.objects.get_or_create(username='demo')
        if created or not demo.check_password('demo1234'):
            demo.set_password('demo1234')
            demo.email = 'demo@example.com'
            demo.first_name = 'Demo'
            demo.last_name = 'User'
            demo.save()
            self.stdout.write('  Created demo user')

        # Admin user
        admin, created = User.objects.get_or_create(username='admin')
        if created or not admin.check_password('admin1234'):
            admin.set_password('admin1234')
            admin.is_staff = True
            admin.is_superuser = True
            admin.email = 'admin@example.com'
            admin.save()
            self.stdout.write('  Created admin user')

        # Products
        products_data = [
            {'name': 'Wireless Headphones', 'description': 'Premium noise-cancelling wireless headphones with 30h battery.', 'price': Decimal('149.99'), 'stock': 50},
            {'name': 'Mechanical Keyboard', 'description': 'RGB mechanical keyboard with Cherry MX switches.', 'price': Decimal('89.99'), 'stock': 30},
            {'name': 'USB-C Hub', 'description': '7-in-1 USB-C hub with HDMI, USB 3.0, and PD charging.', 'price': Decimal('39.99'), 'stock': 100},
            {'name': 'Webcam 1080p', 'description': 'Full HD webcam with built-in microphone and autofocus.', 'price': Decimal('59.99'), 'stock': 75},
            {'name': 'Monitor Stand', 'description': 'Adjustable ergonomic monitor stand with storage drawer.', 'price': Decimal('34.99'), 'stock': 40},
            {'name': 'Mouse Pad XL', 'description': 'Extra-large desk mat for keyboard and mouse, non-slip.', 'price': Decimal('19.99'), 'stock': 200},
        ]

        products = []
        for data in products_data:
            p, _ = Product.objects.get_or_create(name=data['name'], defaults=data)
            products.append(p)
        self.stdout.write(f'  Seeded {len(products)} products')

        # Orders
        if not Order.objects.filter(user=demo).exists():
            order1 = Order.objects.create(user=demo, status='Confirmed')
            OrderItem.objects.create(order=order1, product=products[0], quantity=1)
            OrderItem.objects.create(order=order1, product=products[2], quantity=2)

            order2 = Order.objects.create(user=demo, status='Pending')
            OrderItem.objects.create(order=order2, product=products[1], quantity=1)
            OrderItem.objects.create(order=order2, product=products[5], quantity=3)
            self.stdout.write('  Seeded demo orders')

        self.stdout.write(self.style.SUCCESS('Demo data ready. Login: demo / demo1234'))
