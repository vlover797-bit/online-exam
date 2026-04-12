# False Positive Troubleshooting Guide

## Quick Reference

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| "Looking away" alerts when student looks straight | Threshold too low | Increase `HEAD_YAW_THRESHOLD` to 30+ |
| Multiple faces detected when only one person | Face detection jitter | Increase `FACE_COUNT_HYSTERESIS` to 5 |
| Tab switch alert spam every second | Debounce too short | Increase `ALERT_DEBOUNCE_MS` to 5000 |
| Audio alerts from breathing/typing | Voice threshold too low | Increase `VOICE_DETECTION_THRESHOLD` to 0.10+ |
| No alerts even when student tabs out | Detection disabled | Check if monitoring is enabled |
| Baseline not establishing | First frame has issues | Wait for system to stabilize (< 1 sec) |

---

## Detailed False Positive Analysis

### Issue 1: "Looking Away" Alerts Too Frequently

#### Symptoms
- Alert triggers when student looks straight ahead
- Alert when student has normal eye movements
- Alert from slightly turning head

#### Root Causes
1. **Head Yaw Threshold Too Low** - Default 25° might be too strict for your setup
2. **Baseline Not Properly Established** - Calibration failed
3. **Camera Angle Issues** - Camera not at eye level
4. **Lighting Problems** - Face detection failing intermittently

#### Solutions (in order of effectiveness)

**Solution A: Increase Head Yaw Threshold**
```python
# In proctoring/proctoring_engine.py

CONFIG = {
    'HEAD_YAW_THRESHOLD': 30,  # Increased from 25
    'HEAD_PITCH_THRESHOLD': 25,  # Also increase pitch
}
```
Test: Student can turn head 30° without alert. Reduce if needed.

**Solution B: Increase Time-Based Persistence**
```python
CONFIG = {
    'VIOLATION_PERSISTENCE_TIME': 3.0,  # Increased from 2.0
}
```
Effect: Violation must persist 3 seconds instead of 2.

**Solution C: Improve Baseline Calibration**
Make sure exam starts with:
- Student facing camera directly
- Good lighting on face
- No obstructions (glasses, hair)
- Camera at eye level or slightly above

**Solution D: Adjust Face Detection Sensitivity**
```python
CONFIG = {
    'FACE_DETECTION_MIN_NEIGHBORS': 6,  # Make stricter (higher = stricter)
    'FACE_DETECTION_SCALE': 1.05,       # Finer scale (lower = more detections)
}
```

#### Testing
```bash
# Test in browser console
console.log(window.proctorMonitor.violations)  # Check violations
```

---

### Issue 2: Multiple Faces Alert When Only One Person

#### Symptoms
- "Multiple faces detected" alert but only student on camera
- Alert flickers on/off repeatedly
- Happens when student moves

#### Root Causes
1. **Face Detection Jitter** - Cascade classifier detecting shadows/reflections as faces
2. **Multiple Face Confirmation Too Low** - Only needs 1 frame to confirm
3. **Face Count Hysteresis Too Small** - Median filter not smoothing

#### Solutions

**Solution A: Increase Hysteresis (BEST)**
```python
CONFIG = {
    'FACE_COUNT_HYSTERESIS': 5,  # Use median of 5 frames instead of 3
    'MULTIPLE_FACE_CONFIRMATION_FRAMES': 3,  # Confirm in 3 frames
}
```
Effect: Noise filtered out, real multiple faces still detected.

**Solution B: Stricter Cascade Classifier**
```python
CONFIG = {
    'FACE_DETECTION_MIN_NEIGHBORS': 6,  # Higher = stricter
    'FACE_DETECTION_SCALE': 1.05,  # Finer resolution
}
```

**Solution C: Improve Lighting**
- Avoid shadows on face
- Ensure consistent lighting
- No reflective surfaces near camera

**Solution D: Check Camera Positioning**
- Position away from windows (reduces reflections)
- Mount at eye level
- Ensure clear background

#### Testing
```bash
# Enable debug logging  
# Add to proctoring_engine.py before calling process_frame()
print(f"Face count: {face_count}, Stable: {self.face_detector.get_stable_face_count()}")
```

---

### Issue 3: Audio Alerts from Background Noise

#### Symptoms
- Alert when student typing/breathing
- Alert from air conditioner/fan
- Alert from keyboard tapping
- Alert from paper rustling

#### Root Causes
1. **Voice Detection Threshold Too Low** (Default 0.08 may be too sensitive)
2. **FFT Peak Threshold Too Low** (Too many frequency peaks detected)
3. **Microphone Too Sensitive** (Picking up everything)

#### Solutions

**Solution A: Increase Voice Detection Threshold (BEST)**
```python
CONFIG = {
    'VOICE_DETECTION_THRESHOLD': 0.10,  # Increased from 0.08
    'NOISE_THRESHOLD': 0.03,  # Increased from 0.02
}
```
Effect: Only actual speech triggers analysis, not noise.

**Solution B: Increase FFT Peak Threshold**
```python
CONFIG = {
    'MULTIPLE_SPEAKER_FFT_PEAKS': 10,  # Increased from 8
}
```
Effect: Needs more frequency peaks (more chaotic sound) to trigger.

**Solution C: Increase Persistence Duration**
```python
CONFIG = {
    'VIOLATION_PERSISTENCE_TIME': 3.0,  # Increased from 2.0
}
```
Effect: Background noise must persist 3+ seconds (brief noise ignored).

**Solution D: Reduce Microphone Gain**
- In OS settings, reduce microphone input level
- Move microphone farther from background noise sources

**Solution E: Use Noise Cancellation**
- Enable browser noise cancellation if available
- Use headset with noise cancellation

#### Testing
```javascript
// Check audio levels in browser console
window.proctorMonitor.updateAudioStatus('TEST', 0.08);  // See how 0.08 looks
```

---

### Issue 4: Tab Switch Alert Debouncing

#### Symptoms
- Multiple alerts for single tab switch
- Alert every frame
- Spam of same violation

#### Root Causes
1. **Alert Debounce Too Short** (Default 3000ms might not be enough)
2. **Multiple Violation Loggers** (Both backend and frontend logging)

#### Solutions

**Solution A: Increase Alert Debounce (RECOMMENDED)**
```javascript
// In static/js/proctor_monitor.js
this.ALERT_DEBOUNCE_MS = 5000;  // Increased from 3000 (5 seconds between same violation)
```

**Solution B: Backend Deduplication**
```python
# In proctoring/proctoring_engine.py
# (Already implemented with log_violation debouncing)
# Default 5 second debounce per violation type
```

---

### Issue 5: No Baseline Establishment

#### Symptoms
- "Baseline not established" message
- Looking away detection not working
- System waits at start

#### Root Causes
1. **First Frame Invalid** - Student not in frame on first detection
2. **Face Detection Failing** - Cascade classifier not detecting face
3. **Multiple Faces on Start** - > 1 face detected

#### Solutions

**Solution A: Ensure Student in Frame**
- Inform student to position camera before starting exam
- Have "Ready?" confirmation button

**Solution B: Retry Baseline**
```python
# Add to proctoring/proctoring_engine.py
if not self.baseline_established:
    # Retry up to 10 times (10 frames)
    self.baseline_attempts = getattr(self, 'baseline_attempts', 0) + 1
    if self.baseline_attempts > 10:
        # Force baseline even with poor detection
        self.baseline_established = True
```

**Solution C: Better Lighting**
- Ensure face is well-lit
- Avoid backlighting
- Position light in front of student

---

## System-Wide Tuning Strategy

### Step 1: Start with Balanced Config (Default)
```python
'HEAD_YAW_THRESHOLD': 25,
'FACE_MISSING_TIMEOUT': 3.0,
'VIOLATION_PERSISTENCE_TIME': 2.0,
'VOICE_DETECTION_THRESHOLD': 0.08,
'MULTIPLE_SPEAKER_FFT_PEAKS': 8,
```

### Step 2: Run 1 Week of Exams
- Collect violation logs
- Track false positives
- Note timing patterns

### Step 3: Increase Thresholds If Too Many False Positives
```python
# Make ALL detections less sensitive
'HEAD_YAW_THRESHOLD': 30,  # +5
'VIOLATION_PERSISTENCE_TIME': 3.0,  # +1.0
'VOICE_DETECTION_THRESHOLD': 0.09,  # +0.01
'MULTIPLE_SPEAKER_FFT_PEAKS': 9,  # +1
```

### Step 4: Run Another Week
- Check if false positives reduced
- Check if real violations still caught
- Adjust again if needed

### Step 5: Fine-Tune Individual Detection
- If only audio is noisy, adjust only `VOICE_DETECTION_THRESHOLD`
- If only looking-away is problematic, adjust only `HEAD_YAW_THRESHOLD`
- Never adjust all parameters at once

---

## Detection Sensitivity Matrix

| Setting | Lower = | Higher = |
|---------|---------|----------|
| `HEAD_YAW_THRESHOLD` | More sensitive (< 20° triggers) | Less sensitive (> 30° triggers) |
| `FACE_MISSING_TIMEOUT` | Quicker alert (< 2 sec) | More grace (> 4 sec) |
| `VIOLATION_PERSISTENCE_TIME` | Faster alerts (< 1 sec) | Slower alerts (> 3 sec) |
| `VOICE_DETECTION_THRESHOLD` | Detects more noise (<0.07) | Ignores noise (>0.09) |
| `MULTIPLE_SPEAKER_FFT_PEAKS` | More sensitive (< 7) | Less sensitive (> 10) |
| `FACE_COUNT_HYSTERESIS` | More jitter (= 2) | Smoother (= 5) |

---

## How to Validate Configuration

### Test 1: Solo Student (No Speaking)
```
Expected: No violations (except maybe looking away test)
Run: 30-minute exam solo
Result: Violations should be near 0
```

### Test 2: Reading Test (Looking Down Occasionally)
```
Expected: NO looking away violations
Run: Read from paper while in frame
Result: Few/no violations
```

### Test 3: Deliberate Violations
```
Expected: All violations CAUGHT
Tests:
- Turn head 35° left (should alert)
- Leave frame for 4 seconds (should alert)
- Have 2nd person on camera (should alert immediately)
- Have 2nd person speak on audio (should alert)
Result: All caught within thresholds
```

---

## Monitoring & Metrics

### Daily Check
```python
# Django shell
from proctoring.models import ProctorLog
from django.db.models import Count

# False positive indicator: Many violations of same type in same minute
logs = ProctorLog.objects.filter(
    timestamp__gte=timezone.now() - timedelta(hours=1)
).values('violation_type').annotate(
    count=Count('id'), 
    attempts=Count('attempt', distinct=True)
)

for log in logs:
    violations_per_exam = log['count'] / log['attempts']
    if violations_per_exam > 3:
        print(f"⚠️ {log['violation_type']}: {violations_per_exam:.1f} per exam (HIGH)")
```

### Weekly Report
- Total violations logged
- By type breakdown
- False positive estimate
- Tuning recommendations

---

## Common Mistakes to Avoid

❌ **DON'T**: Change all parameters at once
✅ **DO**: Change one parameter at a time

❌ **DON'T**: Set thresholds too high (miss real violations)
✅ **DO**: Find balance between sensitivity and accuracy

❌ **DON'T**: Ignore lighting and camera setup
✅ **DO**: Ensure good physical setup first

❌ **DON'T**: Disable detections to hide false positives
✅ **DO**: Tune thresholds properly

❌ **DON'T**: Change config during exam
✅ **DO**: Change between exams, test before deploying

---

## When to Contact Support

If after tuning you still have issues:

1. **Document the problem**:
   - Specific violation types causing false positives
   - Environment description (lighting, camera, room)
   - Current CONFIG settings
   - Sample logs

2. **Attach logs**:
   ```bash
   python manage.py dumpdata proctoring.ProctorLog | head -100 > sample_logs.json
   ```

3. **Describe test environment**:
   - Camera model
   - Room lighting (bright/dim)
   - Network type (WiFi/Ethernet)
   - Browser version

4. **Expected behavior**:
   - What violations should/shouldn't happen
   - Student description

---

## Reference: Default Configuration vs. Recommended Adjustments

### If Getting MANY "looking_away" False Positives
```python
# Original
'HEAD_YAW_THRESHOLD': 25

# Adjust to
'HEAD_YAW_THRESHOLD': 30  # Allow more head movement
'VIOLATION_PERSISTENCE_TIME': 3.0,  # Require longer persistence
```

### If Getting MANY "multiple_faces" False Positives
```python
# Original
'MULTIPLE_FACE_CONFIRMATION_FRAMES': 2

# Adjust to
'MULTIPLE_FACE_CONFIRMATION_FRAMES': 4  # Confirm in 4 frames
'FACE_COUNT_HYSTERESIS': 5  # Median of 5 frames
```

### If Getting MANY "multiple_speakers" False Positives
```python
# Original
'VOICE_DETECTION_THRESHOLD': 0.08

# Adjust to  
'VOICE_DETECTION_THRESHOLD': 0.10  # Only detect actual speech
'MULTIPLE_SPEAKER_FFT_PEAKS': 10  # Need more peaks
```

---

**Last Updated**: March 27, 2026
**Version**: 2.0 - Strict Detection with False-Positive Reduction
**Status**: ✅ Ready to Deploy
