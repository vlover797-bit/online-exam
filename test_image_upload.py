import os
import django
import base64
import json
from django.core.files.base import ContentFile
from django.test import Client

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'secure_exam.settings')
django.setup()

from accounts.models import User
from exams.models import Exam, StudentExamAttempt
from proctoring.models import ProctorLog

# Ensure we have a student and an attempt
# Assuming 'role' field exists and 'student' is a valid choice
student, created = User.objects.get_or_create(username='test_student_image', email='test_image@example.com', role='student')
student.set_password('password123')
student.save()

from django.utils import timezone
from datetime import timedelta

# Exam model requires start_time and end_time
now = timezone.now()
exam, created = Exam.objects.get_or_create(
    title='Test Image Exam',
    defaults={
        'duration_minutes': 60,
        'start_time': now,
        'end_time': now + timedelta(hours=1)
    }
)
attempt, created = StudentExamAttempt.objects.get_or_create(student=student, exam=exam)

from io import BytesIO
from PIL import Image

# Generate a valid image
img = Image.new('RGB', (100, 100), color = 'red')
buffered = BytesIO()
img.save(buffered, format="JPEG")
img_str = base64.b64encode(buffered.getvalue()).decode()
dummy_image_b64 = f"data:image/jpeg;base64,{img_str}"

# Use Django Test Client
c = Client()
url = '/proctoring/process_frame/'
data = {
    'image': dummy_image_b64,
    'attempt_id': attempt.id
}

print(f"Sending request to {url} for attempt {attempt.id}...")
response = c.post(url, data=json.dumps(data), content_type='application/json')

print(f"Response status: {response.status_code}")
print(f"Response content: {response.content.decode()}")

# Check if log created
logs = ProctorLog.objects.filter(attempt=attempt).order_by('-timestamp')
if logs.exists():
    latest_log = logs.first()
    print(f"Log created: {latest_log}")
    if latest_log.image_snapshot:
        print(f"Image saved at: {latest_log.image_snapshot.url}")
        # Verify file exists
        if os.path.exists(latest_log.image_snapshot.path):
             print("SUCCESS: Image file exists on disk.")
        else:
             print("FAILURE: Image file not found on disk.")
    else:
        print("FAILURE: Log created but no image saved.")
else:
    print("FAILURE: No log created.")
