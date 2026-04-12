from django.db import models
from django.conf import settings
import uuid

class ProctorLog(models.Model):
    VIOLATION_TYPES = (
        ('face_not_visible', 'Face Not Visible'),
        ('multiple_faces', 'Multiple Faces Detected'),
        ('looking_away', 'Looking Away from Screen'),
        ('tab_switch', 'Tab/Window Switched'),
        ('multiple_speakers', 'Multiple Speakers Detected'),
        ('background_noise', 'Suspicious Background Noise'),
        ('mobile_phone_detected', 'Mobile Phone Detected'),
        ('notebook_detected', 'Notebook Detected'),
    )
    
    SEVERITY_LEVELS = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    )
    
    attempt = models.ForeignKey('exams.StudentExamAttempt', on_delete=models.CASCADE, related_name='proctor_logs')
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    violation_type = models.CharField(max_length=50, choices=VIOLATION_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default='medium')
    image_snapshot = models.ImageField(upload_to='proctor_logs/', blank=True, null=True)
    audio_snapshot = models.FileField(upload_to='proctor_audio/', blank=True, null=True)
    details = models.TextField(blank=True, null=True)
    is_reviewed = models.BooleanField(default=False)
    reviewer_notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['attempt', 'timestamp']),
            models.Index(fields=['violation_type', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.attempt.student.username} - {self.violation_type} at {self.timestamp}"


class MobileSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    session_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_heartbeat = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    ip_address = models.CharField(max_length=50, blank=True, null=True)
    device_type = models.CharField(max_length=50, blank=True, null=True)
    
    class Meta:
        ordering = ['-last_heartbeat']

    def __str__(self):
        return f"MobileSession {self.user.username} - {self.session_token}"


class ExamSessionViolationReport(models.Model):
    """Summary report of all violations during an exam session"""
    
    STATUS_CHOICES = (
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('flagged', 'Flagged for Review'),
    )
    
    attempt = models.OneToOneField('exams.StudentExamAttempt', on_delete=models.CASCADE, related_name='violation_report')
    total_violations = models.IntegerField(default=0)
    high_severity_violations = models.IntegerField(default=0)
    medium_severity_violations = models.IntegerField(default=0)
    low_severity_violations = models.IntegerField(default=0)
    tab_switches = models.IntegerField(default=0)
    face_not_visible_seconds = models.IntegerField(default=0)
    looking_away_instances = models.IntegerField(default=0)
    speaking_instances = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    proctoring_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Violation Report - {self.attempt.student.username}"
    
    def update_from_logs(self):
        """Update report from actual violation logs"""
        logs = self.attempt.proctor_logs.all()
        
        self.total_violations = logs.count()
        self.high_severity_violations = logs.filter(severity='high').count()
        self.medium_severity_violations = logs.filter(severity='medium').count()
        self.low_severity_violations = logs.filter(severity='low').count()
        self.tab_switches = logs.filter(violation_type='tab_switch').count()
        self.looking_away_instances = logs.filter(violation_type='looking_away').count()
        self.speaking_instances = logs.filter(violation_type='multiple_speakers').count()
        
        # Flag for review if high severity violations
        if self.high_severity_violations > 0:
            self.status = 'flagged'
        
        self.save()
