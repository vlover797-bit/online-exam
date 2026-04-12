# Strict Detection Logic - Complete Guide

## Overview

The proctoring system now uses **event-based, threshold-driven detection** with **time-based smoothing** to eliminate false positives while maintaining high accuracy.

---

## 🎯 Detection Features

### 1. **Looking Away Detection (HEAD POSE ESTIMATION)**

#### How It Works
- **Baseline Establishment**: System establishes a "frontal face baseline" when the exam starts
- **Head Rotation Calculation**: Measures yaw (left/right), pitch (up/down), and roll (tilt)
- **Strict Threshold**: Only triggers if head rotated **> 25 degrees** from baseline
- **Time-Based Persistence**: Violation must persist for **2+ seconds** before alert
- **False-Positive Prevention**: Small eye movements and minor head tilts are IGNORED

#### Thresholds
```python
HEAD_YAW_THRESHOLD = 25          # degrees (turn left/right)
HEAD_PITCH_THRESHOLD = 20        # degrees (look up/down)
VIOLATION_PERSISTENCE_TIME = 2.0  # seconds before alert
```

#### Example Scenarios

✅ **NO VIOLATION** (Student is fine)
- Looking straight at camera
- Natural eye movements while reading
- Minor head tilt (< 15 degrees)
- Blinking frequently

❌ **VIOLATION** (Alert triggered)
- Head turned > 25 degrees left/right
- Looking completely away from camera for 2+ seconds
- Continuous head movement away

#### How to Adjust
```python
# In proctoring/proctoring_engine.py, update CONFIG:

# Stricter detection (lower threshold)
'HEAD_YAW_THRESHOLD': 20,  # Trigger if > 20 degrees
'VIOLATION_PERSISTENCE_TIME': 1.5,  # Trigger after 1.5 seconds

# Lenient detection (higher threshold)
'HEAD_YAW_THRESHOLD': 35,  # Allow > 35 degrees
'VIOLATION_PERSISTENCE_TIME': 3.0,  # Require 3 seconds
```

---

### 2. **Multiple Face Detection**

#### How It Works
- **Cascade Classifier**: Detects all faces in each frame
- **Hysteresis Filtering**: Uses median of last 3 frames for stability
- **Confirmation Requirement**: Multiple faces must be detected in 2+ consecutive frames
- **Immediate Alert**: Triggers as HIGHEST PRIORITY violation

#### Thresholds
```python
FACE_DETECTION_MIN_NEIGHBORS = 5   # Cascade strictness (higher = stricter)
MULTIPLE_FACE_CONFIRMATION_FRAMES = 2  # Frames to confirm before alert
```

#### Example Scenarios

✅ **NO VIOLATION**
- One person in frame
- Temporary motion artifact (< 2 frames)
- Reflection in glass

❌ **VIOLATION** (Immediate alert)
- Two people visible in frame
- Faces consistently detected for 2+ frames

#### How to Adjust
```python
# Stricter detection
'FACE_DETECTION_MIN_NEIGHBORS': 6,  # Requires more neighbors
'MULTIPLE_FACE_CONFIRMATION_FRAMES': 3,  # Confirm in 3 frames

# Lenient detection
'FACE_DETECTION_MIN_NEIGHBORS': 4,  # Fewer neighbors needed
'MULTIPLE_FACE_CONFIRMATION_FRAMES': 1,  # Immediate confirmation
```

---

### 3. **Face Not Visible Detection**

#### How It Works
- **Timeout Tracking**: Records when face was last visible
- **Extended Absence**: Triggers if face missing for **> 3 seconds**
- **MEDIUM PRIORITY**: Lower priority than multiple faces

#### Thresholds
```python
FACE_MISSING_TIMEOUT = 3.0  # seconds
```

#### Example Scenarios

✅ **NO VIOLATION**
- Face visible for exam duration
- Brief absence (< 3 seconds)

❌ **VIOLATION** (Alert triggered)
- Student looks away for 3+ seconds without turning head
- Student leaves exam area

#### How to Adjust
```python
# Stricter (quicker detection)
'FACE_MISSING_TIMEOUT': 2.0,  # Alert after 2 seconds

# Lenient
'FACE_MISSING_TIMEOUT': 5.0,  # Allow 5 seconds away
```

---

### 4. **Tab Switching Detection**

#### How It Works
- **Visibility API**: Monitors `document.hidden` state
- **Window Blur Events**: Detects when exam window loses focus
- **IMMEDIATE ALERT**: Triggers right when student leaves tab
- **Cumulative Count**: Tracks total tab switches during exam

#### Triggers
```javascript
- Alt+Tab: Switches to another window ✓ VIOLATION
- Click outside browser: Triggers blur event ✓ VIOLATION
- Another application gets focus ✓ VIOLATION
- Minimize window: Not directly detected (blur catches it)
```

#### How to Adjust (Frontend)
```javascript
// In static/js/proctor_monitor.js

// Increase alert debounce (less spam)
this.ALERT_DEBOUNCE_MS = 5000;  // Min 5 seconds between alerts

// Decrease debounce (more sensitive)
this.ALERT_DEBOUNCE_MS = 1000;  // Alert every 1 second
```

---

### 5. **Multiple Speakers Detection**

#### How It Works
- **FFT Analysis**: Performs Fast Fourier Transform on audio chunk
- **Frequency Peak Detection**: Analyzes frequency spectrum
- **High Threshold**: Requires **> 8 frequency peaks** to trigger
- **RMS Filter**: Only analyzes when volume > 0.08 (speech level)
- **Time-Based Persistence**: Violation must persist **2+ seconds**

#### Thresholds
```python
VOICE_DETECTION_THRESHOLD = 0.08  # RMS level for speech
NOISE_THRESHOLD = 0.02            # Background noise (ignored)
MULTIPLE_SPEAKER_FFT_PEAKS = 8    # Peaks required for multiple speakers
VIOLATION_PERSISTENCE_TIME = 2.0  # seconds before alert
```

#### Example Scenarios

✅ **NO VIOLATION** (No alert)
- Student speaking alone
- Background noise only (< 0.02 RMS)
- Keyboard typing
- Brief noise bursts

❌ **VIOLATION** (Alert after 2+ seconds)
- Clear conversation from 2+ people
- Multiple distinct speaker voices
- Student + background conversation for 2+ seconds

#### How to Adjust
```python
# More sensitive (detects background conversation)
'VOICE_DETECTION_THRESHOLD': 0.06,  # Lower threshold
'MULTIPLE_SPEAKER_FFT_PEAKS': 6,    # Fewer peaks needed

# Less sensitive (ignores most noise)
'VOICE_DETECTION_THRESHOLD': 0.10,  # Higher threshold
'MULTIPLE_SPEAKER_FFT_PEAKS': 10,   # More peaks needed
```

---

## 🔄 Violation Priority Logic

When multiple violations could trigger, the system uses this priority:

```
PRIORITY 1 (HIGHEST): Multiple Faces Detected
   └─ Immediate alert
   └─ Any other detection paused

PRIORITY 2: Face Not Visible (3+ seconds)
   └─ Alert after timeout
   └─ Prevents looking-away detection

PRIORITY 3: Looking Away (> 25 degrees, 2+ seconds)
   └─ Only if exactly one face is present
   └─ Checks head rotation angles

PRIORITY 4 (LOWEST): Multiple Speakers Detected
   └─ Separate audio analysis
   └─ Can occur simultaneously with others
```

---

## 📊 Event-Based Violations (NOT False Positive-Prone)

### Characteristics of Event-Based Detection

✅ **Advantages**
- Violation only triggers when threshold clearly crossed
- Time-based persistence prevents flickers
- Debouncing prevents alert spam
- Clear start/end of violation state
- No random noise triggers alerts

❌ **Old Random Approach (REMOVED)**
- False positives from lighting changes
- Momentary artifacts trigger alerts
- No persistence checks
- Alert spam from detection jitter

### Example: Looking Away

**OLD APPROACH** (removed):
```
Frame 1: Eyes not detected → Alert immediately ❌ FALSE POSITIVE
Frame 2: Eyes detected → No alert
Frame 3: Eyes not detected → Alert ❌ SPAM
```

**NEW STRICT APPROACH**:
```
Frame 1: Head yaw = 5°  → No alert (< 25° threshold)
Frame 2: Head yaw = 8°  → No alert (< 25° threshold)
Frame 3: Head yaw = 27° → Start counting (> 25° threshold)
Frame 4: Head yaw = 30° → Still elevated
  ⏱️ 2 seconds elapsed → ALERT ✓ LEGITIMATE VIOLATION
```

---

## 🛠️ Configuration Reference

### All Configurable Parameters

```python
# proctoring/proctoring_engine.py - CONFIG Dictionary

# Head Pose Detection
HEAD_YAW_THRESHOLD = 25            # degrees (turn left/right)
HEAD_PITCH_THRESHOLD = 20          # degrees (look up/down)
HEAD_ROLL_THRESHOLD = 15           # degrees (head tilt)

# Cascade Classifier Settings
FACE_DETECTION_MIN_NEIGHBORS = 5   # Higher = stricter
FACE_DETECTION_SCALE = 1.1         # Scale factor (lower + stricter)

# Smoothing & Persistence (reduce false positives)
LOOKING_AWAY_THRESHOLD_FRAMES = 30  # Frames before considering looking away
FACE_MISSING_TIMEOUT = 3.0          # Seconds before face_not_visible
VIOLATION_PERSISTENCE_TIME = 2.0    # Seconds violation must persist

# Face Counting Hysteresis
FACE_COUNT_HYSTERESIS = 3           # Use median of last N frames
MULTIPLE_FACE_CONFIRMATION_FRAMES = 2  # Confirm in N consecutive frames

# Audio Thresholds
VOICE_DETECTION_THRESHOLD = 0.08
NOISE_THRESHOLD = 0.02
MULTIPLE_SPEAKER_FFT_PEAKS = 8
MULTIPLE_SPEAKER_VOLUME_MULTIPLIER = 1.5
```

### Recommended Presets

**Strict (High Security)**
```python
'HEAD_YAW_THRESHOLD': 20,
'FACE_MISSING_TIMEOUT': 2.5,
'VIOLATION_PERSISTENCE_TIME': 1.5,
'MULTIPLE_FACE_CONFIRMATION_FRAMES': 1,
'VOICE_DETECTION_THRESHOLD': 0.07,
```

**Balanced (Default - Recommended)**
```python
'HEAD_YAW_THRESHOLD': 25,
'FACE_MISSING_TIMEOUT': 3.0,
'VIOLATION_PERSISTENCE_TIME': 2.0,
'MULTIPLE_FACE_CONFIRMATION_FRAMES': 2,
'VOICE_DETECTION_THRESHOLD': 0.08,
```

**Lenient (Fewer False Positives)**
```python
'HEAD_YAW_THRESHOLD': 35,
'FACE_MISSING_TIMEOUT': 4.0,
'VIOLATION_PERSISTENCE_TIME': 3.0,
'MULTIPLE_FACE_CONFIRMATION_FRAMES': 3,
'VOICE_DETECTION_THRESHOLD': 0.10,
```

---

## 🧪 Testing & Tuning

### How to Test Each Detection Feature

#### 1. Test Looking Away
```
1. Start exam
2. Slowly turn your head 25+ degrees left (hold 2+ seconds)
3. Expect: Alert after 2 seconds
4. Turn back straight
5. Expect: Alert clears
```

#### 2. Test Multiple Faces
```
1. Start exam with one face
2. Have another person enter camera view
3. Expect: Immediate critical alert
4. Remove other person
5. Expect: Alert clears after a few frames
```

#### 3. Test Face Missing
```
1. Start exam with camera on
2. Move away from camera (face disappears)
3. Wait 3+ seconds
4. Expect: Alert after 3 seconds
5. Move back to camera
6. Expect: Alert clears immediately
```

#### 4. Test Multiple Speakers
```
1. Start exam
2. Speak alone (no violation)
3. Have another person talk in background (2+ seconds)
4. Expect: Alert after ~2 seconds
5. Other person stops talking
6. Expect: Alert clears after silence
```

#### 5. Test Tab Switching
```
1. Start exam
2. Press Alt+Tab to switch application
3. Expect: Immediate alert
4. Alt+Tab back to exam
5. Expect: Different alert saying tab returned
```

### Tuning Guide

If you get **FALSE POSITIVES** (alerts when shouldn't happen):
- ❌ Student looking straight: Increase `HEAD_YAW_THRESHOLD` (e.g., 30)
- ❌ Momentary 2-face detection: Increase `MULTIPLE_FACE_CONFIRMATION_FRAMES` (3+)
- ❌ Audio noise triggering alerts: Increase `VOICE_DETECTION_THRESHOLD` (0.10+)
- ❌ Too sensitive to head movement: Increase `VIOLATION_PERSISTENCE_TIME` (3.0+)

If you get **FALSE NEGATIVES** (miss actual violations):
- ✅ Student looking away: Decrease `HEAD_YAW_THRESHOLD` (20)
- ✅ Multiple people enter undetected: Decrease `MULTIPLE_FACE_CONFIRMATION_FRAMES` (1)
- ✅ Background conversation missed: Decrease `VOICE_DETECTION_THRESHOLD` (0.06)
- ✅ Need quicker detection: Decrease `VIOLATION_PERSISTENCE_TIME` (1.0)

---

## 📈 Real-World Scenarios

### Scenario 1: Student Reading from Textbook (At Desk)
```
✓ Student seated at desk
✓ Glancing down occasionally (< 25° pitch)
✓ Eyes visible on camera
✓ Typing answers

Result: NO VIOLATIONS ✅
```

### Scenario 2: Student Talking to Someone Off-Screen
```
✗ Head turned 35° to the side
✗ Maintained for 3+ seconds
✗ Looking away from camera

Result: LOOKING_AWAY VIOLATION ❌
(Also might trigger MULTIPLE_SPEAKERS if that person talks)
```

### Scenario 3: Student Gets Help from Friend
```
✗ Two faces in shot
✗ Detected in multiple frames
✗ Both speaking audibly

Result: MULTIPLE_FACES + MULTIPLE_SPEAKERS VIOLATIONS ❌
(Highest priority: MULTIPLE_FACES alert shows first)
```

### Scenario 4: Student Minimizes/Alt+Tabs
```
✗ Visibility API detects hidden state
✗ Window blur event fires

Result: TAB_SWITCH VIOLATION ❌
(Immediate alert, cumulative count increments)
```

### Scenario 5: Student Briefly Out of Frame (< 3 sec)
```
✗ Face missing
✗ < 3 seconds

Result: NO VIOLATION ✅
(Grace period for bathroom, water, etc.)

✗ Face missing  
✗ > 3 seconds

Result: FACE_NOT_VISIBLE VIOLATION ❌
```

---

## 🔧 Advanced Configuration

### Disable Specific Detections

```python
# In proctoring/proctoring_engine.py, modify process_frame()

# Disable looking away detection
if False:  # Disable
    pose_status = self.head_pose_estimator.detect_looking_away(...)

# Disable multiple face detection
if False:  # Disable
    if face_status['status'] == "MULTIPLE_FACES_DETECTED":
        violations.extend(face_status['violations'])

# Disable face missing detection  
'FACE_MISSING_TIMEOUT': float('inf'),  # Never trigger
```

### Per-Exam Configuration

```python
# In proctoring_views.py, pass CONFIG to session

session = ProctoringSessions()
session.config = {
    'exam_type': 'strict',  # strict, balanced, lenient
    'allow_head_movement': False,  # Stricter
    'voice_sensitivity': 'high'
}
```

---

## 📊 Monitoring Detection Health

### Check Detection Status in Real-Time

```javascript
// In browser console during exam
window.proctorMonitor.getViolationsSummary()

// Output:
{
  total: 3,
  by_severity: {high: 1, medium: 2, low: 0},
  tab_switches: 1,
  violations_list: [...]
}
```

### Backend Logs

```python
# In Django shell
python manage.py shell

from proctoring.models import ProctorLog
logs = ProctorLog.objects.filter(attempt__id=123)
logs.values('violation_type', 'severity').annotate(Count('id'))

# Output violations by type
```

---

## 🎓 Best Practices

1. **Calibrate per environment**: Different rooms/lighting may need different thresholds
2. **Test before deploying**: Run full exam cycle in your environment
3. **Start with balanced settings**: Use defaults, then adjust based on feedback
4. **Monitor false positives**: Review logs weekly for tuning needs
5. **Inform students**: Explain what gets flagged so they avoid accidental violations
6. **Have appeals process**: False positives can happen despite tuning

---

## 📚 Algorithm Details

### Head Pose Estimation Formula

```
yaw = (current_center_x - baseline_center_x) / face_width * 30
pitch = (avg_eye_y - baseline_center_y) / face_height * 25
```

### Face Count Hysteresis
```
stable_count = median(last_3_frame_counts)
```
Example: [1, 1, 2] → median = 1 ✅ (noise filtering)

### FFT Peak Detection
```
fft = FFT(audio_chunk)
peaks = frequencies_where(magnitude > 30% of max)
violation = (peaks > threshold)
```

### Debouncing (Frontend)
```
last_alert[violation_type] = now
if now - last_alert < DEBOUNCE_TIME:
    send_to_backend()  # Log but don't alert
```

---

**Status**: ✅ Production Ready with False-Positive Reduction
**Version**: 2.0 - Strict Detection
**Last Updated**: March 27, 2026
