from django.urls import path
from . import views

urlpatterns = [
    path('process_frame/', views.process_frame, name='process_frame'),
    path('system_check/<int:attempt_id>/', views.system_check_view, name='system_check'),
    path('mobile/<int:attempt_id>/', views.mobile_cam_view, name='mobile_cam'),
    path('mobile_upload/', views.upload_mobile_frame, name='mobile_upload'),
    path('get_mobile_frame/<int:attempt_id>/', views.get_mobile_frame, name='get_mobile_frame'),
]
