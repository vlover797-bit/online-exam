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
import socket

# Global dictionary to store latest frames from mobile devices
# Key: attempt_id, Value: (timestamp, frame_data)
mobile_streams = {}

def get_local_ip():
    """Get the local machine IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

import os
import numpy as np

# Load Face and Eye Detector
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

# Load YOLO
try:
    yolo_net = cv2.dnn.readNet("proctoring/models/yolov3-tiny.weights", "proctoring/models/yolov3-tiny.cfg")
    layer_names = yolo_net.getLayerNames()
    try:
        output_layers = [layer_names[i - 1] for i in yolo_net.getUnconnectedOutLayers()]
    except Exception:
        output_layers = [layer_names[i[0] - 1] for i in yolo_net.getUnconnectedOutLayers()]
    with open("proctoring/models/coco.names", "r") as f:
        coco_classes = [line.strip() for line in f.readlines()]
except Exception as e:
    yolo_net = None
    coco_classes = []
    output_layers = []

@csrf_exempt
def process_frame(request):
    if request.method == 'POST':
        try:
            # Robust JSON parse
            try:
                data = json.loads(request.body)
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': f'Invalid JSON: {str(e)}'}, status=400)

            image_data = data.get('image')
            attempt_id = data.get('attempt_id')
            
            if not image_data or not attempt_id:
                return JsonResponse({'status': 'error', 'message': 'Missing image/attempt_id'}, status=400)

            # Robust image decode using PIL (since cv2.imdecode is failing in this env)
            try:
                if ';base64,' in image_data:
                    _, imgstr = image_data.split(';base64,', 1)
                else:
                    imgstr = image_data
                
                imgstr = imgstr.strip()
                encoded_data = base64.b64decode(imgstr)
                
                # Save to temp file to bypass OpenCV 4.11.0 numpy bugs
                import os
                temp_filename = f"temp_frame_{uuid.uuid4()}.jpg"
                with open(temp_filename, "wb") as f:
                    f.write(encoded_data)
                
                frame = cv2.imread(temp_filename)
                gray = cv2.imread(temp_filename, cv2.IMREAD_GRAYSCALE)
                
                # Cleanup temp file
                if os.path.exists(temp_filename):
                    os.remove(temp_filename)
                
                if frame is None or gray is None:
                    return JsonResponse({'status': 'error', 'message': 'Image load failed'}, status=400)
            except Exception as decode_err:
                print(f"FAILED process_frame file-based: {decode_err}")
                return JsonResponse({'status': 'error', 'message': f'Image parse error: {str(decode_err)}'}, status=400)
            
            violation = None
            violation_details = None
            
            # Use Haar Cascade for quick face counting - moderate strictness
            faces = face_cascade.detectMultiScale(gray, 1.1, 6) 
            
            # Use global state for small hysteresis (confirmation)
            if not hasattr(process_frame, 'face_history'):
                process_frame.face_history = {}
            
            attempt_history = process_frame.face_history.get(attempt_id, [])
            attempt_history.append(len(faces))
            if len(attempt_history) > 3:
                attempt_history.pop(0)
            process_frame.face_history[attempt_id] = attempt_history

            # Check if multiple faces are consistently detected
            stable_multiple = len(attempt_history) >= 2 and all(count > 1 for count in attempt_history[-2:])
            
            if stable_multiple:
                violation = 'multiple_faces'
                violation_details = f"Multiple faces detected: {len(faces)}"
            elif len(faces) == 0:
                if len(attempt_history) >= 2 and all(count == 0 for count in attempt_history[-2:]):
                    violation = 'no_face'
                    violation_details = "Face not detected in student view"

            # Use YOLO to confirm if multiple people are in laptop view
            if yolo_net is not None:
                blob_l = cv2.dnn.blobFromImage(frame, 0.00392, (320, 320), (0, 0, 0), True, crop=False)
                yolo_net.setInput(blob_l)
                outs_l = yolo_net.forward(output_layers)
                
                person_count = 0
                for out in outs_l:
                    for detection in out:
                        scores = detection[5:]
                        class_id = np.argmax(scores)
                        confidence = scores[class_id]
                        if confidence > 0.45 and coco_classes and class_id < len(coco_classes):
                            if coco_classes[class_id] == "person":
                                person_count += 1

                if person_count > 1:
                    violation = 'multiple_faces'
                    violation_details = f"Detected {person_count} people in monitoring frame"

            # 2. Now Check Mobile Frame for Objects and Faces (Aggressive Monitoring)
            detected_objects = []
            mobile_person_count = 0
            
            if str(attempt_id) in mobile_streams:
                timestamp, mobile_image_data = mobile_streams[str(attempt_id)]
                if time.time() - timestamp < 15: # Increased timeout to 15s to be more forgiving
                    try:
                        # Decode mobile frame with file-based fallback
                        try:
                            if ';base64,' in mobile_image_data:
                                _, m_imgstr = mobile_image_data.split(';base64,', 1)
                            else:
                                m_imgstr = mobile_image_data
                            m_encoded_data = base64.b64decode(m_imgstr)
                            
                            m_temp = f"m_temp_{uuid.uuid4()}.jpg"
                            with open(m_temp, "wb") as f:
                                f.write(m_encoded_data)
                            m_frame = cv2.imread(m_temp)
                            if os.path.exists(m_temp):
                                os.remove(m_temp)
                        except Exception as e:
                            print(f"Mobile file-decode error: {e}")
                            m_frame = None
                        
                        if m_frame is not None:
                            # Face detection on mobile (person in room)
                            m_gray = cv2.cvtColor(m_frame, cv2.COLOR_BGR2GRAY)
                            m_faces = face_cascade.detectMultiScale(m_gray, 1.05, 3) # Even more sensitive for room view
                            if len(m_faces) > 0:
                                if "face" not in detected_objects: detected_objects.append("face")
                                if not violation:
                                    violation = 'unauthorized_person_behind'
                                    violation_details = f"Unauthorized person (face) detected in background: {len(m_faces)}"

                            # Object detection for mobile room monitoring
                            if yolo_net is not None:
                                blob_m = cv2.dnn.blobFromImage(m_frame, 0.00392, (320, 320), (0, 0, 0), True, crop=False)
                                yolo_net.setInput(blob_m)
                                outs_m = yolo_net.forward(output_layers)
                                
                                for out in outs_m:
                                    for detection in out:
                                        scores = detection[5:]
                                        class_id = np.argmax(scores)
                                        confidence = scores[class_id]
                                        # HIGH SENSITIVITY for proctoring (0.4)
                                        if confidence > 0.4 and coco_classes and class_id < len(coco_classes):
                                            class_name = coco_classes[class_id]
                                            
                                            if class_name not in detected_objects:
                                                detected_objects.append(class_name)
                                            
                                            if class_name == "person":
                                                mobile_person_count += 1
                                            
                                            # Electronic Devices & Study Materials
                                            electronics = ["cell phone", "laptop", "tvmonitor", "mouse", "keyboard", "remote"]
                                            if class_name in electronics and not violation:
                                                violation = 'electronic_device_detected'
                                                violation_details = f"DETECTED ELECTRONIC DEVICE ({class_name}) IN ROOM"
                                            
                                            elif class_name == "book" and not violation:
                                                violation = 'notebook_detected'
                                                violation_details = "DETECTED UNAUTHORIZED STUDY MATERIAL (BOOK)"
                                
                                # If multiple people in room view
                                if mobile_person_count > 0 and not violation:
                                    violation = 'unauthorized_person_behind'
                                    violation_details = "Unauthorized person(s) detected in background by room camera"
                    except Exception as e:
                        print(f"Error in mobile processing: {e}")
            
            # Response prep
            response_data = {'status': 'ok', 'processed': True, 'face_count': len(faces)}
            if detected_objects:
                response_data['objects'] = detected_objects

            if violation:
                # Log to DB
                attempt = StudentExamAttempt.objects.get(id=attempt_id)
                
                # Create file from base64
                image_content = ContentFile(base64.b64decode(imgstr))
                filename = f"violation_{attempt.student.username}_{uuid.uuid4()}.jpg"
                
                # Use specific details if available
                details = locals().get('violation_details', f"Detected {violation}")
                
                ProctorLog.objects.create(
                    attempt=attempt,
                    violation_type=violation,
                    details=details,
                    image_snapshot=ContentFile(image_content.read(), name=filename)
                )
                response_data.update({
                    'status': 'violation', 
                    'type': violation,
                    'message': details
                })
            
            return JsonResponse(response_data)
            
        except Exception as e:
            print(f"CRITICAL ERROR in process_frame: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

def system_check_view(request, attempt_id):
    attempt = get_object_or_404(StudentExamAttempt, id=attempt_id)
    # Generate URL for mobile with IP address for QR scanning from other devices
    # Set smart mobile URL: Public domain on Vercel, Local IP on local dev
    if os.environ.get('VERCEL'):
        # On Vercel, use the public domain
        mobile_url = request.build_absolute_uri(f"/proctoring/mobile/{attempt.id}/")
    else:
        # On local dev, use the local IP so phone can connect via WiFi
        local_ip = get_local_ip()
        port = request.META.get('SERVER_PORT', '8000')
        mobile_url = f"http://{local_ip}:{port}/proctoring/mobile/{attempt.id}/"
    
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

