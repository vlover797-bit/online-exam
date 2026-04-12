import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'secure_exam.settings')
django.setup()

from accounts.models import User

# Update all users to password123
users = User.objects.all()
for user in users:
    user.set_password('password123')
    user.save()
    print(f"Updated password for {user.username} to password123")

# Create default users if they don't exist
default_users = [
    ('faculty_admin', 'faculty', 'faculty@example.com'),
    ('student_user', 'student', 'student@example.com'),
]

for username, role, email in default_users:
    if not User.objects.filter(username=username).exists():
        user = User.objects.create_user(username=username, password='password123', role=role, email=email)
        print(f"Created {role} user: {username} with password123")
    else:
        user = User.objects.get(username=username)
        user.set_password('password123')
        user.save()
        print(f"Updated {username} to password123")

print("\n✅ All users configured with password: password123")
print("\nAvailable test accounts:")
for username, role, email in default_users:
    print(f"  {username} (role: {role}) - password: password123")
