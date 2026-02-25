import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'secure_exam.settings')
django.setup()

from accounts.models import User

def create_user(username, password, role, email):
    try:
        if not User.objects.filter(username=username).exists():
            User.objects.create_user(username=username, password=password, role=role, email=email)
            print(f"Created {role} user: {username} / {password}")
        else:
            print(f"{role} user '{username}' already exists")
    except Exception as e:
        print(f"Error creating {username}: {e}")

create_user('faculty', 'faculty123', 'faculty', 'faculty@example.com')
create_user('student', 'student123', 'student', 'student@example.com')

from exams.models import Exam, Question, Option
from django.utils import timezone
from datetime import timedelta

def create_sample_exam():
    if not Exam.objects.filter(title="Sample Fraud Detection Test").exists():
        start_time = timezone.now()
        end_time = start_time + timedelta(hours=2)
        exam = Exam.objects.create(
            title="Sample Fraud Detection Test",
            description="Run this test to verify the proctoring system. Ensure your webcam is enabled.",
            start_time=start_time,
            end_time=end_time,
            duration_minutes=60,
            is_active=True
        )
        
        q1 = Question.objects.create(exam=exam, text="What is the capital of France?", marks=10)
        Option.objects.create(question=q1, text="Berlin", is_correct=False)
        Option.objects.create(question=q1, text="Paris", is_correct=True)
        Option.objects.create(question=q1, text="Madrid", is_correct=False)
        Option.objects.create(question=q1, text="Rome", is_correct=False)
        
        q2 = Question.objects.create(exam=exam, text="Which planet is known as the Red Planet?", marks=10)
        Option.objects.create(question=q2, text="Mars", is_correct=True)
        Option.objects.create(question=q2, text="Venus", is_correct=False)
        Option.objects.create(question=q2, text="Jupiter", is_correct=False)
        
        print("Created sample exam 'Sample Fraud Detection Test'")
    else:
        print("Sample exam already exists")

create_sample_exam()
