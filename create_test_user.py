import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'secure_exam.settings')
django.setup()

from accounts.models import User
from django.core.management.base import BaseCommand

try:
    if not User.objects.filter(username='faculty_admin').exists():
        User.objects.create_user(username='faculty_admin', password='password123', role='faculty', email='faculty@example.com')
        print("Created faculty user: faculty_admin / password123")
    else:
        print("Faculty user 'faculty_admin' already exists")
except Exception as e:
    print(f"Error: {e}")
