"""
Strict Exam Proctoring Engine - FINAL VERSION
Detects ONLY 4 Violation Types:
1. multiple_faces (>1 face for 2+ seconds) - CRITICAL
2. no_face (student not visible for 3+ seconds) - CRITICAL
3. unauthorized_voice (speech for 2+ seconds) - HIGH
4. tab_switch (browser tab switch detected frontend) - HIGH
5. looking_down (head down towards desk/phone) - HIGH

No eye detection. No head pose estimation. Clean and strict.
"""

import cv2
import numpy as np
from collections import deque
import time
from datetime import datetime


# ============================================================================
# CONFIGURATION
# ============================================================================
CONFIG = {
    # Face Detection
    'FACE_DETECTION_MIN_NEIGHBORS': 8,  # Cascade parameter (higher = stricter)
    'FACE_DETECTION_SCALE': 1.1,        # Cascade parameter
    
    # Multiple Face Detection
    'MULTIPLE_FACE_CONFIRMATION_FRAMES': 3,
    'MULTIPLE_FACE_PERSISTENCE_TIME': 3.0,
    'FACE_COUNT_HYSTERESIS': 5,  # Number of frames for median smoothing
    
    # No Face Detection (face disappeared)
    'NO_FACE_PERSISTENCE_TIME': 3.0,  # Alert after 3 seconds no face
    
    # Looking Down Detection (face position in frame)
    'LOOKING_DOWN_THRESHOLD': 0.65,  # Face center Y > 65% of frame height
    'LOOKING_DOWN_PERSISTENCE_TIME': 2.0,
    
    # Audio/Voice Detection
    'VOICE_DETECTION_THRESHOLD': 0.08,
    'NOISE_THRESHOLD': 0.02,
    'VOICE_PERSISTENCE_TIME': 2.0,
    'SAMPLE_RATE': 16000,
}


class FaceDetector:
    """
    Detects: 
    - Multiple faces (violation)
    - No face (violation after 3 sec)
    - Single face OK
    - Face looking down (potential phone usage)
    """
    
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.current_face_count = 0
        self.multiple_face_start_time = None
        self.is_multiple_face_detected = False
        self.no_face_start_time = None
        self.looking_down_start_time = None
        self.is_looking_down = False
        self.face_positions = deque(maxlen=5)  # Track face positions
        self.face_count_history = deque(maxlen=CONFIG.get('FACE_COUNT_HYSTERESIS', 5))
        
    def detect_faces(self, frame):
        """
        Detect faces and analyze their position
        Returns: (face_count, face_locations, gray_frame)
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray, 
            scaleFactor=CONFIG['FACE_DETECTION_SCALE'],
            minNeighbors=10, # Increased from 8 for better precision
            minSize=(50, 50),
            maxSize=(400, 400)
        )
        
        self.current_face_count = len(faces)
        self.face_count_history.append(len(faces))
        
        # Track face position for looking_down detection
        if len(faces) == 1:
            x, y, w, h = faces[0]
            face_center_y = y + h / 2
            frame_height = frame.shape[0]
            y_ratio = face_center_y / frame_height
            self.face_positions.append(y_ratio)
        else:
            self.face_positions.clear()
        
        return self.current_face_count, faces, gray
    
    def get_stable_face_count(self):
        """
        Returns the median face count over the last few frames to filter jitter.
        """
        if not self.face_count_history:
            return 0
        return int(np.median(list(self.face_count_history)))

    def get_face_status(self):
        """
        Analyze face status and detect violations
        """
        face_count = self.get_stable_face_count()
        violations = []
        status = "OK"
        
        # VIOLATION 1: Multiple Faces
        if face_count > 1:
            if not self.is_multiple_face_detected:
                self.is_multiple_face_detected = True
                self.multiple_face_start_time = time.time()
            else:
                duration = time.time() - self.multiple_face_start_time
                if duration >= CONFIG['MULTIPLE_FACE_PERSISTENCE_TIME']:
                    violations.append({
                        'type': 'multiple_faces',
                        'severity': 'critical',
                        'message': f'Multiple faces detected - UNAUTHORIZED PERSON',
                        'timestamp': datetime.now().isoformat()
                    })
                    status = "MULTIPLE_FACES"
        else:
            self.is_multiple_face_detected = False
            self.multiple_face_start_time = None
        
        # VIOLATION 2: No Face (disappeared)
        if face_count == 0:
            if self.no_face_start_time is None:
                self.no_face_start_time = time.time()
            else:
                duration = time.time() - self.no_face_start_time
                if duration >= CONFIG['NO_FACE_PERSISTENCE_TIME']:
                    violations.append({
                        'type': 'no_face',
                        'severity': 'critical',
                        'message': f'Face not visible for 3+ seconds - Student left frame',
                        'timestamp': datetime.now().isoformat()
                    })
                    status = "NO_FACE"
        else:
            self.no_face_start_time = None
        
        # VIOLATION 3: Looking Down (head towards desk/phone)
        if len(self.face_positions) > 0:
            avg_y_pos = np.mean(list(self.face_positions))
            is_looking_down = avg_y_pos > CONFIG['LOOKING_DOWN_THRESHOLD']
            
            if is_looking_down:
                if not self.is_looking_down:
                    self.is_looking_down = True
                    self.looking_down_start_time = time.time()
                else:
                    duration = time.time() - self.looking_down_start_time
                    if duration >= CONFIG['LOOKING_DOWN_PERSISTENCE_TIME']:
                        violations.append({
                            'type': 'looking_down',
                            'severity': 'high',
                            'message': 'Head down towards desk/phone detected',
                            'timestamp': datetime.now().isoformat()
                        })
                        status = "LOOKING_DOWN"
            else:
                self.is_looking_down = False
                self.looking_down_start_time = None
        
        # Set status if no violations yet
        if status == "OK":
            if face_count == 1:
                status = "OK"
            elif face_count == 0:
                status = "NO_FACE"
        
        return {
            'status': status,
            'face_count': face_count,
            'violations': violations
        }


class AudioAnalyzer:
    """
    Simple voice/noise detection.
    Detects unauthorized voice/abnormal sounds above threshold for 2+ seconds.
    Ignores ambient background noise.
    """
    
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate
        self.noise_threshold = CONFIG['NOISE_THRESHOLD']
        self.voice_threshold = CONFIG['VOICE_DETECTION_THRESHOLD']
        
        # Voice detection persistence
        self.voice_start_time = None
        self.is_voice_detected = False
        self.violation_triggered = False
        
    def analyze_audio_chunk(self, audio_chunk):
        """
        Analyze audio chunk for unauthorized voice.
        Triggers violation if voice detected for 2+ seconds.
        
        Returns: {status, violations, volume_level}
        """
        if audio_chunk is None or len(audio_chunk) == 0:
            return {
                'status': 'NO_AUDIO',
                'violations': [],
                'volume_level': 0.0
            }
        
        # Convert to numpy if needed
        if not isinstance(audio_chunk, np.ndarray):
            audio_chunk = np.array(audio_chunk, dtype=np.float32)
        
        # Calculate RMS for volume detection
        rms = np.sqrt(np.mean(audio_chunk ** 2))
        
        violations = []
        status = "SILENT"
        
        # Simple threshold-based detection
        if rms > self.voice_threshold:
            status = "SPEAKING"
            
            # Voice detected - track persistence
            if not self.is_voice_detected:
                # Just detected voice - start timer
                self.is_voice_detected = True
                self.voice_start_time = time.time()
                self.violation_triggered = False
            else:
                # Already in voice state - check if 2 seconds have passed
                duration = time.time() - self.voice_start_time
                if duration >= CONFIG['VOICE_PERSISTENCE_TIME'] and not self.violation_triggered:
                    # Violation triggered after 2 seconds of voice
                    violations.append({
                        'type': 'unauthorized_voice',
                        'severity': 'high',
                        'message': 'Unauthorized voice/abnormal sound detected',
                        'timestamp': datetime.now().isoformat(),
                        'volume_level': float(rms)
                    })
                    self.violation_triggered = True
        elif rms > self.noise_threshold:
            status = "BACKGROUND_NOISE"
        else:
            status = "SILENT"
            # Back to silent - reset detection
            if self.is_voice_detected:
                self.is_voice_detected = False
                self.violation_triggered = False
                self.voice_start_time = None
        
        return {
            'status': status,
            'volume_level': float(rms),
            'violations': violations
        }



class ProctoringSessions:
    """
    Simplified proctoring session manager.
    
    Detects ONLY 3 violation types:
    1. Multiple faces detected (>1 for 2+ seconds) - CRITICAL
    2. Tab switching / visibility change - HIGH  
    3. Unauthorized voice/abnormal sound (2+ seconds) - HIGH
    
    Event-Based violations:
    - Only trigger when threshold is clearly crossed
    - Use time-based persistence (2 seconds)
    - Clean, stable logic without false positives
    - NO head pose estimation
    - NO eye movement tracking
    - NO looking away detection
    """
    
    def __init__(self):
        self.face_detector = FaceDetector()
        self.audio_analyzer = AudioAnalyzer()
        
        self.violations_log = []
        self.session_start = datetime.now()
        self.frame_count = 0
        
        # Deduplication: track last violation of each type
        self.last_violation_log = {}
        
    def process_frame(self, frame_data):
        """
        Process video frame for face violations.
        Only detects: Multiple faces (>1 for 2+ seconds)
        
        Returns: {violations, face_count, frame_count}
        """
        self.frame_count += 1
        violations = []
        
        # Decode frame if needed
        if isinstance(frame_data, str):
            import base64
            try:
                frame_data = base64.b64decode(frame_data.split(',')[1])
                nparr = np.frombuffer(frame_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            except:
                return {'violations': [], 'error': 'Frame decode failed'}
        else:
            frame = frame_data
        
        if frame is None or frame.size == 0:
            return {'violations': [], 'error': 'Invalid frame'}
        
        # Face Detection
        face_count, faces, gray = self.face_detector.detect_faces(frame)
        face_status = self.face_detector.get_face_status()
        
        # Check for violations
        if face_status['status'] == "MULTIPLE_FACES":
            violations.extend(face_status['violations'])
        
        # Log violations
        for violation in violations:
            self.log_violation(
                violation['type'],
                violation['severity'],
                violation.get('message', '')
            )
        
        return {
            'violations': violations,
            'face_count': face_count,
            'frame_count': self.frame_count,
            'face_status': face_status['status']
        }
    
    def process_audio(self, audio_chunk):
        """
        Process audio chunk for unauthorized voice.
        Only detects: Unauthorized voice for 2+ seconds
        
        Returns: {violations, audio_status, volume_level}
        """
        audio_status = self.audio_analyzer.analyze_audio_chunk(audio_chunk)
        
        # Log violations
        violations = audio_status['violations']
        for violation in violations:
            self.log_violation(
                violation['type'],
                violation['severity'],
                violation.get('message', '')
            )
        
        return {
            'violations': violations,
            'audio_status': audio_status['status'],
            'volume_level': audio_status['volume_level']
        }
    
    def log_violation(self, violation_type, severity, message):
        """
        Log a violation with deduplication to avoid spamming.
        Only log if this is a new violation or enough time has passed.
        """
        current_time = time.time()
        last_log = self.last_violation_log.get(violation_type, {})
        
        # Debounce: Don't log same violation type within 5 seconds
        if current_time - last_log.get('time', 0) < 5:
            return
        
        violation = {
            'timestamp': datetime.now().isoformat(),
            'type': violation_type,
            'severity': severity,
            'message': message
        }
        
        self.violations_log.append(violation)
        self.last_violation_log[violation_type] = {'time': current_time}
    
    def get_session_summary(self):
        """Get comprehensive session summary."""
        return {
            'total_violations': len(self.violations_log),
            'session_duration': (datetime.now() - self.session_start).total_seconds(),
            'frame_count': self.frame_count,
            'violations_by_type': self._count_violations_by_type(),
            'violations_by_severity': self._count_violations_by_severity(),
            'recent_violations': self.violations_log[-10:] if self.violations_log else []
        }
    
    def _count_violations_by_type(self):
        """Count violations by type."""
        counts = {}
        for v in self.violations_log:
            vtype = v['type']
            counts[vtype] = counts.get(vtype, 0) + 1
        return counts
    
    def _count_violations_by_severity(self):
        """Count violations by severity."""
        counts = {'low': 0, 'medium': 0, 'high': 0}
        for v in self.violations_log:
            severity = v.get('severity', 'low')
            counts[severity] = counts.get(severity, 0) + 1
        return counts
