from django.contrib import admin
from .models import ProctorLog, ExamSessionViolationReport, MobileSession

@admin.register(ProctorLog)
class ProctorLogAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'violation_type', 'severity', 'timestamp', 'is_reviewed')
    list_filter = ('violation_type', 'severity', 'timestamp', 'is_reviewed')
    search_fields = ('attempt__student__username', 'details')
    readonly_fields = ('timestamp', 'attempt')
    fieldsets = (
        ('Violation Info', {'fields': ('attempt', 'violation_type', 'severity')}),
        ('Details', {'fields': ('details', 'image_snapshot', 'audio_snapshot')}),
        ('Review', {'fields': ('is_reviewed', 'reviewer_notes')}),
        ('Timestamp', {'fields': ('timestamp',)}),
    )

@admin.register(ExamSessionViolationReport)
class ExamSessionViolationReportAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'total_violations', 'high_severity_violations', 'status', 'updated_at')
    list_filter = ('status', 'updated_at')
    search_fields = ('attempt__student__username',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Exam', {'fields': ('attempt',)}),
        ('Violation Summary', {
            'fields': ('total_violations', 'high_severity_violations', 'medium_severity_violations', 'low_severity_violations')
        }),
        ('Violation Details', {
            'fields': ('tab_switches', 'face_not_visible_seconds', 'looking_away_instances', 'speaking_instances')
        }),
        ('Status & Notes', {
            'fields': ('status', 'proctoring_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Update from logs when saved"""
        obj.update_from_logs()
        super().save_model(request, obj, form, change)

@admin.register(MobileSession)
class MobileSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_active', 'device_type', 'created_at', 'last_heartbeat')
    list_filter = ('is_active', 'device_type', 'created_at')
    search_fields = ('user__username', 'ip_address')
    readonly_fields = ('session_token', 'created_at', 'last_heartbeat')
    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Session', {'fields': ('session_token', 'is_active')}),
        ('Device', {'fields': ('device_type', 'ip_address')}),
        ('Timestamps', {'fields': ('created_at', 'last_heartbeat')}),
    )

