/**
 * Real-Time Exam Proctoring System - Frontend Module
 * Handles: Eye gaze detection, tab switching, audio monitoring, real-time alerts
 * 
 * STRICT VIOLATION LOGIC:
 * - Multiple faces: Immediate critical alert
 * - Face not visible: Alert after 3+ seconds
 * - Looking away: Alert only if head > 25 degrees (backend checks)
 * - Multiple speakers: Alert after 2+ second persistence
 * - Tab switch: Immediate alert + logging
 */

class ExamProctorMonitor {
    constructor(attemptId, examId) {
        this.attemptId = attemptId;
        this.examId = examId;
        this.violations = [];
        this.isMonitoring = false;
        this.tabSwitchCount = 0;
        
        // Alert debouncing: prevent spam
        this.lastViolationAlert = {};
        this.ALERT_DEBOUNCE_MS = 3000; // Min 3 seconds between same violation type alerts
        
        // Thresholds
        this.WARNING_THRESHOLD = 5; // Number of high-severity violations before warning
        this.CRITICAL_THRESHOLD = 15; // Critical violations
        
        // Initialize components
        this.setupEventListeners();
        this.setupVisibilityTracking();
        this.setupAudioMonitoring();
    }
    
    /**
     * Setup document event listeners
     */
    setupEventListeners() {
        // Tab/Window visibility change
        document.addEventListener('visibilitychange', () => this.handleVisibilityChange());
        
        // Window focus changes
        window.addEventListener('focus', () => this.logEvent('window_focused'));
        window.addEventListener('blur', () => this.handleWindowBlur());
        
        // Prevent right-click to block inspect element
        document.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            this.logViolation('right_click_attempted', 'low', 'Attempted to use right-click');
        });
        
        // Detect F12 and other dev tools shortcuts
        document.addEventListener('keydown', (e) => this.handleDeveloperToolsShortcut(e));
    }
    
    /**
     * Handle window blur (another app in focus)
     */
    handleWindowBlur() {
        if (this.isMonitoring) {
            this.logViolation('window_blur', 'high', 'Exam window lost focus - application switched');
            this.showAlert(
                '⚠️ Window Lost Focus',
                'You have switched to another application. This has been logged.',
                'danger'
            );
        }
    }
    
    /**
     * Handle visibility change (tab switching)
     */
    handleVisibilityChange() {
        if (document.hidden) {
            this.tabSwitchCount++;
            this.logViolation(
                'tab_switch',
                'high',
                `Tab switched away (Total: ${this.tabSwitchCount})`
            );
            this.showAlert(
                '⚠️ Tab Switch Detected',
                'You have switched away from this exam tab. This has been logged as a violation.',
                'danger'
            );
        } else {
            this.logEvent('tab_returned');
        }
    }
    
    /**
     * Handle developer tools keyboard shortcuts
     */
    handleDeveloperToolsShortcut(e) {
        // F12
        if (e.key === 'F12') {
            e.preventDefault();
            this.logViolation('dev_tools_attempt', 'high', 'F12 key pressed');
            this.showAlert('⚠️ Developer Tools Blocked', 'Attempt to open developer tools blocked.', 'warning');
        }
        
        // Ctrl+Shift+I (Windows/Linux) or Cmd+Option+I (Mac)
        if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'I') {
            e.preventDefault();
            this.logViolation('dev_tools_attempt', 'high', 'Ctrl+Shift+I pressed');
        }
        
        // Ctrl+Shift+C (Inspector)
        if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'C') {
            e.preventDefault();
            this.logViolation('dev_tools_attempt', 'high', 'Inspector shortcut attempted');
        }
    }
    
    /**
     * Setup visibility tracking
     */
    setupVisibilityTracking() {
        // Monitor page visibility
        setInterval(() => {
            if (document.hidden && this.isMonitoring) {
                this.logEvent('page_hidden_detected');
            }
        }, 1000);
    }
    
    /**
     * Setup audio monitoring
     */
    setupAudioMonitoring() {
        if (!navigator.mediaDevices) {
            console.warn('Audio monitoring not available');
            return;
        }
        
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                this.setupAudioAnalyzer(stream);
            })
            .catch(err => {
                console.warn('Microphone access denied:', err);
                this.logViolation('microphone_denied', 'medium', 'Microphone access was denied');
            });
    }
    
    /**
     * Setup Web Audio API for voice analysis
     */
    setupAudioAnalyzer(stream) {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const analyser = audioContext.createAnalyser();
        const microphone = audioContext.createMediaStreamSource(stream);
        const scriptProcessor = audioContext.createScriptProcessor(4096, 1, 1);
        
        analyser.fftSize = 256;
        microphone.connect(analyser);
        analyser.connect(scriptProcessor);
        scriptProcessor.connect(audioContext.destination);
        
        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        
        // Audio analysis parameters
        let silenceCount = 0;
        let speakingCount = 0;
        const silenceThreshold = 50; // dB threshold
        const speechThreshold = 80; // dB threshold
        
        scriptProcessor.onaudioprocess = () => {
            analyser.getByteFrequencyData(dataArray);
            
            // Calculate average frequency
            const average = dataArray.reduce((a, b) => a + b) / bufferLength;
            
            // Detect speech vs silence
            if (average > speechThreshold) {
                speakingCount++;
                silenceCount = 0;
                this.updateAudioStatus('SPEAKING', average);
                
            } else if (average < silenceThreshold) {
                silenceCount++;
                speakingCount = 0;
                this.updateAudioStatus('SILENT', average);
                
            } else {
                // Background noise or ambient sound
                this.updateAudioStatus('BACKGROUND_NOISE', average);
            }
            
            // Detect multiple speakers (sudden spikes with complex frequency)
            if (this.detectMultipleSpeakers(dataArray)) {
                this.logViolation(
                    'multiple_speakers',
                    'high',
                    'Multiple speakers or suspicious audio detected'
                );
                this.showAlert('🔊 Alert', 'Multiple voices detected. Ensure you are the only person speaking.', 'danger');
            }
        };
    }
    
    /**
     * Detect multiple speakers from audio frequency data
     */
    detectMultipleSpeakers(frequencyArray) {
        // Find peaks in frequency array
        const peaks = [];
        for (let i = 1; i < frequencyArray.length - 1; i++) {
            if (frequencyArray[i] > frequencyArray[i - 1] && frequencyArray[i] > frequencyArray[i + 1]) {
                peaks.push(i);
            }
        }
        
        // Multiple speakers have distinct frequency peaks
        return peaks.length > 8; // Threshold for multiple speakers
    }
    
    /**
     * Update audio status display
     */
    updateAudioStatus(status, level) {
        const audioStatus = document.getElementById('audio-status');
        if (audioStatus) {
            audioStatus.innerText = `Audio: ${status} (Level: ${Math.round(level)})`;
            audioStatus.style.color = status === 'SPEAKING' ? 'orange' : 'green';
        }
    }
    
    /**
     * Process video frame for violations
     */
    processVideoFrame(canvas, stream) {
        const ctx = canvas.getContext('2d');
        const video = document.querySelector('video#webcam');
        
        // Draw current frame
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        // Send to backend for analysis
        canvas.toBlob((blob) => {
            const reader = new FileReader();
            reader.onloadend = () => {
                this.sendFrameToBackend(reader.result);
            };
            reader.readAsDataURL(blob);
        }, 'image/jpeg', 0.8);
    }
    
    /**
     * Send frame to backend for analysis
     * Handles violations from strict detection logic
     */
    sendFrameToBackend(imageData) {
        fetch('/proctoring/process_frame/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCookie('csrftoken')
            },
            body: JSON.stringify({
                image: imageData,
                attempt_id: this.attemptId
            })
        })
        .then(res => res.json())
        .then(data => {
            if (data.violations && data.violations.length > 0) {
                // Process each violation from backend
                data.violations.forEach(violation => {
                    const severity = violation.severity || 'medium';
                    const message = violation.message || `${violation.type} detected`;
                    
                    // Log the violation with debouncing
                    this.logViolation(
                        violation.type,
                        severity,
                        message
                    );
                });
            }
            
            // Update detection status for UI
            if (data.face_status) {
                this.updateDetectionStatus(data);
            }
        })
        .catch(err => {
            console.error('Frame processing error:', err);
            this.logEvent(`Frame processing failed: ${err.message}`);
        });
    }
    
    /**
     * Update detection status display
     */
    updateDetectionStatus(data) {
        const statusDiv = document.getElementById('detection-status');
        if (!statusDiv) return;
        
        const face_count = data.face_count || 0;
        const face_status = data.face_status || 'UNKNOWN';
        
        let statusHtml = `
            <div class="detection-info">
                <span>Faces: ${face_count}</span> |
                <span>Status: ${face_status.replace(/_/g, ' ')}</span> |
                <span>Baseline: ${data.baseline_established ? '✓' : '⏳'}</span>
            </div>
        `;
        
        statusDiv.innerHTML = statusHtml;
        
        // Color code based on status
        if (face_status === 'MULTIPLE_FACES') {
            statusDiv.style.color = 'red';
        } else if (face_status === 'NO_FACE') {
            statusDiv.style.color = 'orange';
        } else if (face_status === 'OK') {
            statusDiv.style.color = 'green';
        }
    }
    
    /**
     * Log violation to database
     * Includes debouncing to prevent alert spam
     */
    logViolation(type, severity, message) {
        // Skip duplicate alerts within debounce period
        const now = Date.now();
        const lastAlert = this.lastViolationAlert[type] || 0;
        
        if (now - lastAlert < this.ALERT_DEBOUNCE_MS) {
            // Still in debounce period, just log but don't alert
            this.violations.push({
                type, severity, message,
                timestamp: new Date().toISOString()
            });
            return;
        }
        
        // Update last violation time
        this.lastViolationAlert[type] = now;
        
        // Add to violations log
        this.violations.push({
            type,
            severity,
            message,
            timestamp: new Date().toISOString()
        });
        
        // Send to backend
        fetch('/proctoring/log_violation/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCookie('csrftoken')
            },
            body: JSON.stringify({
                attempt_id: this.attemptId,
                violation_type: type,
                severity: severity,
                details: message
            })
        })
        .catch(err => console.error('Violation logging error:', err));
        
        // Determine alert styling and display
        let alertType = 'warning';
        if (severity === 'high') alertType = 'danger';
        if (severity === 'low') alertType = 'info';
        
        this.showAlert(
            `⚠️ Violation: ${type.replace(/_/g, ' ').toUpperCase()}`,
            message,
            alertType
        );
        
        // Check severity thresholds
        const highViolations = this.violations.filter(v => v.severity === 'high').length;
        
        if (highViolations >= this.CRITICAL_THRESHOLD) {
            this.triggerEmergencyStop();
        } else if (highViolations >= this.WARNING_THRESHOLD) {
            this.showAlert(
                '🚨 WARNING',
                `You have ${highViolations} high-severity violations. Continued violations will terminate your exam.`,
                'danger',
                true
            );
        }
    }
    
    /**
     * Emergency stop exam if critical violations
     */
    triggerEmergencyStop() {
        this.showAlert(
            '🚨 EXAM TERMINATED',
            'Too many violations detected. Your exam has been terminated.',
            'danger',
            true
        );
        
        // Disable exam submission and redirect
        setTimeout(() => {
            window.location.href = `/exams/${this.examId}/result/`;
        }, 5000);
    }
    
    /**
     * Show alert to student (with improved styling)
     */
    showAlert(title, message, type = 'warning', isPersistent = false) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        
        // Add styling for different alert types
        alertDiv.style.cssText = `
            margin: 10px 0;
            padding: 15px;
            border-radius: 4px;
            font-weight: 500;
            ${type === 'danger' ? 'animation: pulse 0.5s ease-in-out;' : ''}
        `;
        
        alertDiv.innerHTML = `
            <div>
                <strong>${title}</strong>
                ${message ? '<br>' + message : ''}
            </div>
            ${!isPersistent ? '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' : ''}
        `;
        
        const container = document.querySelector('.container') || document.querySelector('main') || document.body;
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-dismiss non-persistent alerts
        if (!isPersistent) {
            setTimeout(() => {
                if (alertDiv.parentElement) {
                    alertDiv.remove();
                }
            }, 5000);
        }
    }
    
    /**
     * Log event (non-violation)
     */
    logEvent(eventType) {
        // Log to console for debugging
        console.log(`[PROCTORING] ${eventType} at ${new Date().toISOString()}`);
    }
    
    /**
     * Get CSRF token
     */
    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                cookie = cookie.trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    /**
     * Start monitoring
     */
    startMonitoring() {
        this.isMonitoring = true;
        console.log('Proctoring monitoring started');
    }
    
    /**
     * Stop monitoring
     */
    stopMonitoring() {
        this.isMonitoring = false;
        console.log('Proctoring monitoring stopped');
    }
    
    /**
     * Get violations summary
     */
    getViolationsSummary() {
        return {
            total: this.violations.length,
            by_severity: {
                high: this.violations.filter(v => v.severity === 'high').length,
                medium: this.violations.filter(v => v.severity === 'medium').length,
                low: this.violations.filter(v => v.severity === 'low').length
            },
            tab_switches: this.tabSwitchCount,
            violations_list: this.violations
        };
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const attemptId = document.querySelector('[data-attempt-id]')?.getAttribute('data-attempt-id');
    const examId = document.querySelector('[data-exam-id]')?.getAttribute('data-exam-id');
    
    if (attemptId && examId) {
        window.proctorMonitor = new ExamProctorMonitor(attemptId, examId);
        window.proctorMonitor.startMonitoring();
    }
});
