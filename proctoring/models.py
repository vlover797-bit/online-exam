from django.db import models
from django.conf import settings
import uuid

class ProctorLog(models.Model):
    attempt = models.ForeignKey('exams.StudentExamAttempt', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    violation_type = models.CharField(max_length=50) # 'no_face', 'multiple_faces', 'mobile_detected', etc.
    image_snapshot = models.ImageField(upload_to='proctor_logs/')
    details = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.attempt.student.username} - {self.violation_type} at {self.timestamp}"

class MobileSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    session_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"MobileSession {self.user.username} - {self.session_token}"
