"""
Proctoring API Views
Handles violation logging, frame processing, and real-time monitoring
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
import base64
import json
import numpy as np
import cv2
from datetime import datetime, timedelta

from exams.models import StudentExamAttempt
from .models import ProctorLog, ExamSessionViolationReport
from .proctoring_engine import ProctoringSessions


# Global proctoring sessions tracker
proctoring_sessions = {}


@csrf_exempt
@require_http_methods(["POST"])
def log_violation(request):
    """
    Log a violation directly from frontend or backend analysis
    Expected JSON: {
        "attempt_id": 123,
        "violation_type": "tab_switch",
        "severity": "high",
        "details": "Student switched tabs"
    }
    """
    try:
        data = json.loads(request.body)
        attempt_id = data.get('attempt_id')
        violation_type = data.get('violation_type')
        severity = data.get('severity', 'medium')
        details = data.get('details', '')
        
        if not attempt_id or not violation_type:
            return JsonResponse({'status': 'error', 'message': 'Missing required fields'}, status=400)
        
        attempt = StudentExamAttempt.objects.get(id=attempt_id)
        
        # Create violation log
        violation_log = ProctorLog.objects.create(
            attempt=attempt,
            violation_type=violation_type,
            severity=severity,
            details=details
        )
        
        # Update violation report
        report, created = ExamSessionViolationReport.objects.get_or_create(attempt=attempt)
        report.update_from_logs()
        
        return JsonResponse({
            'status': 'success',
            'violation_id': violation_log.id,
            'message': f'{violation_type} logged successfully'
        })
    
    except StudentExamAttempt.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Attempt not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def process_frame(request):
    """
    Process video frame for violations
    Expected JSON: {
        "image": "data:image/jpeg;base64,...",
        "attempt_id": 123
    }
    """
    try:
        data = json.loads(request.body)
        image_data = data.get('image')
        attempt_id = data.get('attempt_id')
        
        if not image_data or not attempt_id:
            return JsonResponse({'status': 'error', 'message': 'Missing data'}, status=400)
        
        # Get or create proctoring session
        if attempt_id not in proctoring_sessions:
            proctoring_sessions[attempt_id] = ProctoringSessions()
        
        session = proctoring_sessions[attempt_id]
        
        # Decode image
        try:
            format, imgstr = image_data.split(';base64,')
            nparr = np.frombuffer(base64.b64decode(imgstr), np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Image decode failed: {str(e)}'}, status=400)
        
        # Process frame
        analysis_result = session.process_frame(frame)
        
        # Log any violations
        attempt = StudentExamAttempt.objects.get(id=attempt_id)
        violations = analysis_result.get('violations', [])
        
        for violation in violations:
            ProctorLog.objects.create(
                attempt=attempt,
                violation_type=violation.get('type'),
                severity=violation.get('severity', 'medium'),
                details=violation.get('message'),
                image_snapshot=None  # Could save snapshot if needed
            )
        
        # Get current violation status
        face_status = analysis_result.get('face_status', {})
        gaze_status = analysis_result.get('gaze_status')
        
        response_data = {
            'status': 'ok' if not violations else 'violation',
            'frame_processed': True,
            'face_count': face_status.get('face_count', 0),
            'face_status': face_status.get('status'),
            'violations': violations
        }
        
        if violations:
            response_data['violation_type'] = violations[0]['type'] if violations else None
            response_data['message'] = violations[0]['message'] if violations else None
        
        return JsonResponse(response_data)
    
    except StudentExamAttempt.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Attempt not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def process_audio(request):
    """
    Process audio chunk for voice violations
    Expected JSON: {
        "audio_chunk": [...],
        "attempt_id": 123,
        "sample_rate": 16000
    }
    """
    try:
        data = json.loads(request.body)
        attempt_id = data.get('attempt_id')
        audio_chunk = data.get('audio_chunk', [])
        sample_rate = data.get('sample_rate', 16000)
        
        if not attempt_id or not audio_chunk:
            return JsonResponse({'status': 'error', 'message': 'Missing audio data'}, status=400)
        
        # Get or create proctoring session
        if attempt_id not in proctoring_sessions:
            proctoring_sessions[attempt_id] = ProctoringSessions()
        
        session = proctoring_sessions[attempt_id]
        
        # Convert list to numpy array
        audio_array = np.array(audio_chunk, dtype=np.float32)
        
        # Process audio
        audio_result = session.process_audio(audio_array)
        
        # Log any violations
        attempt = StudentExamAttempt.objects.get(id=attempt_id)
        violations = audio_result.get('violations', [])
        
        for violation in violations:
            ProctorLog.objects.create(
                attempt=attempt,
                violation_type=violation.get('type'),
                severity=violation.get('severity', 'medium'),
                details=violation.get('message')
            )
        
        return JsonResponse({
            'status': 'ok' if not violations else 'violation',
            'audio_status': audio_result['audio_status'],
            'violations': violations
        })
    
    except StudentExamAttempt.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Attempt not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_violation_report(request, attempt_id):
    """
    Get violation report for an exam attempt
    """
    try:
        attempt = StudentExamAttempt.objects.get(id=attempt_id, student=request.user)
        report, created = ExamSessionViolationReport.objects.get_or_create(attempt=attempt)
        report.update_from_logs()
        
        return JsonResponse({
            'status': 'success',
            'report': {
                'total_violations': report.total_violations,
                'high_severity': report.high_severity_violations,
                'medium_severity': report.medium_severity_violations,
                'low_severity': report.low_severity_violations,
                'tab_switches': report.tab_switches,
                'looking_away_instances': report.looking_away_instances,
                'status': report.status,
                'violations': list(
                    attempt.proctor_logs.values(
                        'id', 'timestamp', 'violation_type', 'severity', 'details'
                    )
                )
            }
        })
    
    except StudentExamAttempt.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Attempt not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_proctoring_stats(request, attempt_id):
    """
    Get real-time proctoring statistics
    """
    try:
        attempt = StudentExamAttempt.objects.get(id=attempt_id, student=request.user)
        
        # Get violation counts
        violation_counts = {}
        for violation in ProctorLog.objects.filter(attempt=attempt):
            vtype = violation.violation_type
            violation_counts[vtype] = violation_counts.get(vtype, 0) + 1
        
        # Time in exam
        time_in_exam = (datetime.now() - attempt.start_time).total_seconds() / 60  # minutes
        
        return JsonResponse({
            'status': 'success',
            'stats': {
                'total_violations': attempt.proctor_logs.count(),
                'violation_types': violation_counts,
                'time_in_exam_minutes': time_in_exam,
                'is_completed': attempt.is_completed
            }
        })
    
    except StudentExamAttempt.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Attempt not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def submit_exam_with_violations(request, exam_id):
    """
    Submit exam and finalize violation report
    """
    try:
        from exams.models import Exam
        
        exam = Exam.objects.get(id=exam_id)
        attempt = StudentExamAttempt.objects.get(exam=exam, student=request.user)
        
        # Finalize violation report
        report, created = ExamSessionViolationReport.objects.get_or_create(attempt=attempt)
        report.update_from_logs()
        report.status = 'completed'
        report.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Exam submitted successfully',
            'violation_report': {
                'total_violations': report.total_violations,
                'status': report.status,
                'flagged': report.status == 'flagged'
            }
        })
    
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
