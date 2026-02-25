from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
import cv2
import numpy as np
import base64
from .models import ProctorLog
from exams.models import StudentExamAttempt
import json
from django.core.files.base import ContentFile
import uuid
import time

# Global dictionary to store latest frames from mobile devices
# Key: attempt_id, Value: (timestamp, frame_data)
mobile_streams = {}

# Load Face Detector
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

@csrf_exempt
def process_frame(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            image_data = data.get('image')
            attempt_id = data.get('attempt_id')
            
            if not image_data or not attempt_id:
                return JsonResponse({'status': 'error', 'message': 'Missing data'}, status=400)

            # Decode image
            format, imgstr = image_data.split(';base64,') 
            nparr = np.frombuffer(base64.b64decode(imgstr), np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Convert to grayscale for detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            violation = None
            if len(faces) == 0:
                violation = 'no_face'
            elif len(faces) > 1:
                violation = 'multiple_faces'
            
            # Simple gaze/head pose check (mock logic for now as full gaze is complex without dlib/mediapipe full integration)
            # real implementation would use solvePnP with facial landmarks.
            
            if violation:
                # Log to DB
                attempt = StudentExamAttempt.objects.get(id=attempt_id)
                
                # Create file from base64
                image_content = ContentFile(base64.b64decode(imgstr))
                filename = f"violation_{attempt.student.username}_{uuid.uuid4()}.jpg"
                
                ProctorLog.objects.create(
                    attempt=attempt,
                    violation_type=violation,
                    details=f"Detected {len(faces)} faces.",
                    image_snapshot=ContentFile(image_content.read(), name=filename)
                )
                return JsonResponse({'status': 'violation', 'type': violation})
            
            return JsonResponse({'status': 'ok'})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

def system_check_view(request, attempt_id):
    attempt = get_object_or_404(StudentExamAttempt, id=attempt_id)
    # Generate URL for mobile
    mobile_url = request.build_absolute_uri(f'/proctoring/mobile/{attempt.id}/')
    
    return render(request, 'exams/system_check.html', {
        'attempt': attempt,
        'mobile_url': mobile_url
    })

def mobile_cam_view(request, attempt_id):
    return render(request, 'proctoring/mobile_cam.html', {'attempt_id': attempt_id})

@csrf_exempt
def upload_mobile_frame(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            image_data = data.get('image')
            attempt_id = data.get('attempt_id')
            
            if image_data and attempt_id:
                # Store latest frame with timestamp
                mobile_streams[str(attempt_id)] = (time.time(), image_data)
                print(f"Received frame for attempt {attempt_id}")
                return JsonResponse({'status': 'ok'})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error'}, status=400)

def get_mobile_frame(request, attempt_id):
    # Retrieve latest frame for this attempt
    stream_data = mobile_streams.get(str(attempt_id))
    
    if stream_data:
        timestamp, image_data = stream_data
        # If frame is older than 10 seconds, consider it disconnected
        if time.time() - timestamp < 10:
            return JsonResponse({'status': 'ok', 'image': image_data})
    
    return JsonResponse({'status': 'offline'})

