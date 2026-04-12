# Online Exam Proctoring System - Complete Documentation

## Overview

A comprehensive AI-powered exam proctoring system built with Django and JavaScript that provides real-time monitoring with:
- Eye gaze detection
- Single face enforcement
- Tab switching detection
- Voice monitoring
- Real-time alerts and violation logging

---

## Architecture

### Backend (Django)

**File Structure:**
```
proctoring/
├── proctoring_engine.py    # AI/CV logic
├── proctoring_views.py     # API endpoints
├── models.py               # Database models
├── urls.py                 # URL routing
└── views.py                # Original views
```

**Key Components:**

1. **ProctoringSessions** - Main orchestrator
   - Manages proctoring state
   - Coordinates all detection modules
   - Logs violations

2. **FaceDetector** - Face detection and tracking
   - Detects face count in frame
   - Tracks face visibility duration
   - Flags: no face, multiple faces

3. **EyeGazeDetector** - Eye and gaze analysis
   - Detects eye visibility
   - Determines head pose
   - Flags: looking away from screen
   - Minimizes false positives with frame history

4. **AudioAnalyzer** - Voice and audio analysis
   - Analyzes RMS (volume levels)
   - Detects multiple speakers
   - Analyzes frequency characteristics
   - Flags: background noise, multiple speakers

### Frontend (JavaScript)

**File:** `static/js/proctor_monitor.js`

**Key Class: ExamProctorMonitor**
- Tab switching detection
- Developer tools prevention
- Audio monitoring setup
- Real-time violation logging
- Alert management

---

## Database Models

### ProctorLog
Stores individual violation events with:
- Violation type (face_not_visible, multiple_faces, looking_away, tab_switch, etc.)
- Severity level (low, medium, high)
- Timestamp
- Image/audio snapshot (optional)
- Review status and notes

### ExamSessionViolationReport
Summary report per exam attempt with:
- Total violation count
- Severity breakdown
- Specific violation counts
- Status (in_progress, completed, flagged)
- Auto-flagged if high severity violations detected

### MobileSession
Tracks mobile proctor device sessions with:
- Session token
- Device info
- Last heartbeat
- IP address

---

## API Endpoints

### 1. Log Violation
```
POST /proctoring/log_violation/
Request: {
    "attempt_id": 123,
    "violation_type": "tab_switch",
    "severity": "high",
    "details": "Student switched to browser tab"
}
Response: {
    "status": "success",
    "violation_id": 456
}
```

### 2. Process Frame
```
POST /proctoring/process_frame/
Request: {
    "image": "data:image/jpeg;base64,...",
    "attempt_id": 123
}
Response: {
    "status": "ok|violation",
    "face_count": 1,
    "violations": [...]
}
```

### 3. Process Audio
```
POST /proctoring/process_audio/
Request: {
    "audio_chunk": [float, float, ...],
    "attempt_id": 123,
    "sample_rate": 16000
}
Response: {
    "status": "ok|violation",
    "audio_status": "SPEAKING|SILENT|...",
    "violations": [...]
}
```

### 4. Get Violation Report
```
GET /proctoring/violation_report/<attempt_id>/
Response: {
    "status": "success",
    "report": {
        "total_violations": 5,
        "high_severity": 2,
        "tab_switches": 1,
        "violations": [...]
    }
}
```

### 5. Get Proctoring Stats (Real-time)
```
GET /proctoring/proctoring_stats/<attempt_id>/
Response: {
    "status": "success",
    "stats": {
        "total_violations": 5,
        "violation_types": {"tab_switch": 1, "looking_away": 2},
        "time_in_exam_minutes": 25
    }
}
```

---

## Violation Types & Severity

| Type | Severity | Threshold | Action |
|------|----------|-----------|--------|
| face_not_visible | MEDIUM | 3+ seconds | Warning |
| multiple_faces | HIGH | Any time | Alert |
| looking_away | MEDIUM | 15+ frames | Warning |
| tab_switch | HIGH | Any time | Alert + Log |
| multiple_speakers | HIGH | Detected | Alert |
| background_noise | MEDIUM | Sustained | Warning |
| dev_tools_attempt | HIGH | Any time | Block + Log |
| right_click_attempt | LOW | Any time | Log |

---

## Frontend Integration

### HTML Integration
```html
<!-- Add to exam page -->
<script src="{% static 'js/proctor_monitor.js' %}"></script>
<div data-attempt-id="{{ attempt.id }}" data-exam-id="{{ exam.id }}">
    <!-- Exam content -->
    <div id="audio-status"></div>
    <canvas id="canvas" style="display:none;"></canvas>
</div>
```

### Starting Proctoring
```javascript
// Automatically initialized on DOM ready
window.proctorMonitor.startMonitoring();

// Get violations summary
const summary = window.proctorMonitor.getViolationsSummary();
console.log(summary);
// Output:
// {
//   total: 5,
//   by_severity: {high: 2, medium: 2, low: 1},
//   tab_switches: 1,
//   violations_list: [...]
// }
```

---

## Configuration & Thresholds

### Face Detection
- `face_timeout`: 3 seconds without face = violation
- `scaleFactor`: 1.1 (increase for faster detection, decrease for accuracy)
- `minNeighbors`: 5 (higher = more accurate, slower)
- `maxSize`: 500x500 pixels

### Eye Gaze
- `threshold_frames`: 15 consecutive frames away = violation
- `looking_away_threshold`: 0.3
- Frame history: 10 frames

### Audio Analysis
- `voice_threshold`: 0.08 RMS
- `noise_threshold`: 0.02 RMS
- `silence_duration`: tracked for context
- FFT analysis for frequency peaks (multiple speakers)

### Violation Thresholds
- `WARNING_THRESHOLD`: 3 violations before escalation
- `CRITICAL_THRESHOLD`: 10 violations = exam termination

---

## Performance Optimizations

### Backend
1. **Frame Processing**: 
   - Resize frames to 640x480 before processing
   - Skip frames (process every 2nd frame) for real-time
   - Use C++ OpenCV for fast detection

2. **Audio Analysis**:
   - Use FFT with window size 256
   - Process 4096 sample chunks
   - Avoid redundant frequency analysis

3. **Database**:
   - Index on (attempt, timestamp)
   - Batch save logs
   - Archive old logs periodically

### Frontend
1. **Video Capture**:
   - Canvas drawing at 1 FPS
   - JPEG compression 0.8 quality
   - Send frames every 2 seconds

2. **Audio Processing**:
   - ScriptProcessor 4096 samples
   - Avoid memory leaks in audio context
   - Resample down to 16kHz if needed

???

## False Positive Minimization

### Eye Gaze Detection
- Multi-frame averaging (need 15 frames sustained)
- Tolerance for small head movements
- Only trigger on significant eye movement

### Face Detection
- Face history deque (tracks last 30 frames)
- Hysteresis in detection
- Grace period after face is first lost

### Audio Analysis
- RMS thresholding (not raw amplitude)
- Frequency peak analysis for type
- Recent history window

---

## Security Features

### Frontend Protections
1. **Prevent Tab Switching**
   - Detect `visibilitychange` events
   - Detect `blur` events
   - Log and alert on each switch

2. **Prevent Developer Tools**
   - Block F12
   - Block Ctrl+Shift+I
   - Block Ctrl+Shift+C
   - Block right-click context menu

3. **Prevent Frame Escape**
   - Disable navigation
   - Prevent new windows
   - Lock to fullscreen (optional)

### Backend Validation
1. **Verify Student**
   - Must be logged in
   - Must own the attempt
   - Validate CSRF tokens

2. **Verify Attempt**
   - Must be active (not completed)
   - Must be within exam time window
   - Validate frame timestamps

---

## Admin Dashboard Integration

### Faculty Views
```python
# In Django admin:
class ProctorLogInline(admin.TabularInline):
    model = ProctorLog
    readonly_fields = ('timestamp', 'violation_type', 'severity')

class ExamSessionViolationReportAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'total_violations', 'status', 'updated_at')
    list_filter = ('status', 'created_at')
    search_fields = ('attempt__student__username',)
    inlines = [ProctorLogInline]
```

### Violation Review Workflow
1. Faculty sees flagged exams
2. Reviews violation video snapshots
3. Can override violation (mark as false positive)
4. Add reviewer notes
5. Final decision on exam validity

---

## Troubleshooting

### Face Detection Issues
- **Problem:** Too many false positives
  - **Solution:** Increase `minNeighbors` to 7-8
  
- **Problem:** Misses faces
  - **Solution:** Decrease `scaleFactor` to 1.05, increase `minNeighbors`

### Audio Issues
- **Problem:** Detects music as multiple speakers
  - **Solution:** Increase `FFT peak threshold`
  
- **Problem:** Misses soft speech
  - **Solution:** Decrease `voice_threshold` to 0.06

### Performance Issues
- **Problem:** Slow frame processing
  - **Solution:** Reduce FPS, skip frames, smaller resolution
  
- **Problem:** CPU spike during audio
  - **Solution:** Reduce sample rate to 8kHz, larger chunks

---

## Future Enhancements

1. **Gaze Tracking**
   - Eye tracking API for precise gaze direction
   - Detect reading answer sheets

2. **Behavioral Analysis**
   - Anomaly detection using ML
   - Predictive violation flagging

3. **Mobile Device Monitoring**
   - Real-time rear camera monitoring
   - 360° room scanning

4. **Blockchain Logging**
   - Immutable violation records
   - Cryptographic verification

---

## License & Security

**Production Deployment Checklist:**
- [ ] Change SECRET_KEY in settings.py
- [ ] Set DEBUG = False
- [ ] Use HTTPS with valid certificates
- [ ] Set ALLOWED_HOSTS properly
- [ ] Enable CSRF protection
- [ ] Hash violation snapshots
- [ ] Archive old violation data
- [ ] Set up logging to external service
- [ ] Regular security audits
- [ ] Employee access controls

---

## Support & Contact

For issues, feature requests, or security concerns:
- Review logs: `/proctoring/logs/`
- Check admin violation reports
- Run system diagnostics
- Contact development team
