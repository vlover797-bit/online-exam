from django.urls import path
from . import views
from .proctoring_views import (
    log_violation,
    process_frame,
    process_audio,
    get_violation_report,
    get_proctoring_stats,
    submit_exam_with_violations
)

urlpatterns = [
    # Original endpoints
    path('process_frame/', views.process_frame, name='process_frame'),
    path('system_check/<str:attempt_id>/', views.system_check_view, name='system_check'),
    path('mobile/<str:attempt_id>/', views.mobile_cam_view, name='mobile_cam'),
    path('mobile_upload/', views.upload_mobile_frame, name='mobile_upload'),
    path('get_mobile_frame/<str:attempt_id>/', views.get_mobile_frame, name='get_mobile_frame'),
    
    # New proctoring API endpoints
    path('log_violation/', log_violation, name='log_violation'),
    path('process_audio/', process_audio, name='process_audio'),
    path('violation_report/<str:attempt_id>/', get_violation_report, name='violation_report'),
    path('proctoring_stats/<str:attempt_id>/', get_proctoring_stats, name='proctoring_stats'),
    path('submit_exam/<str:exam_id>/', submit_exam_with_violations, name='submit_with_violations'),
]

