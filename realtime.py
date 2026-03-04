import cv2
import time
import json
import sys
import base64
import requests
from fall_core import FallDetectorMulti
from config import FPS, WINDOW_SIZE, V_THRESH, DY_THRESH, ASPECT_RATIO_THRESH, ALERT_COOLDOWN


# Backend server URL - change this to match your backend IP
BACKEND_URL = "http://192.168.1.27:3000/api/fall-detection/webhook"


def send_fall_alert_http(frame, camera_id="CAM_01", location="PHÒNG KHÁCH"):
    """
    Send fall detection alert via HTTP POST to backend
    Backend will then broadcast to WebSocket clients
    """
    # Encode frame to base64
    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    frame_base64 = base64.b64encode(buffer).decode('utf-8')
    
    # Create alert payload
    alert = {
        'type': 'FALL_DETECTED',
        'camera': camera_id,
        'location': location,
        'frame_base64': frame_base64,
        'timestamp': time.time()
    }
    
    try:
        # Send HTTP POST to backend
        response = requests.post(BACKEND_URL, json=alert, timeout=2)
        if response.status_code == 200:
            print(f"[✓] Alert sent successfully at {time.strftime('%H:%M:%S')}")
        else:
            print(f"[✗] Alert failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"[✗] Connection error: {e}")


def process_realtime_camera(camera_id=0, location="PHÒNG KHÁCH"):
    detector = FallDetectorMulti(
        window_size=WINDOW_SIZE,
        fps=FPS,
        v_thresh=V_THRESH,
        dy_thresh=DY_THRESH,
        ar_thresh=ASPECT_RATIO_THRESH,
    )
    cap = cv2.VideoCapture(camera_id)
    prev_time = time.time()
    last_alert_time = 0  # Track when last alert was sent
    
    # Frame buffer to capture post-fall frames
    fall_detected_time = None
    post_fall_delay = 0.5  # Wait 0.5 seconds after detection to capture
    pending_fall_frame = None
    
    print("\n" + "="*60)
    print("🎥 FALL DETECTION SYSTEM - REAL-TIME MONITORING")
    print("="*60)
    print(f"📹 Camera: {camera_id} | 📍 Location: {location}")
    print(f"⚙️  Settings: Window={WINDOW_SIZE} frames, FPS={FPS}, Cooldown={ALERT_COOLDOWN}s")
    print(f"🎯 Thresholds: Velocity={V_THRESH}, Drop={DY_THRESH}, AspectRatio={ASPECT_RATIO_THRESH}")
    print(f"⏱️  Post-fall delay: {post_fall_delay}s (capture when on ground)")
    print(f"🔗 Backend: {BACKEND_URL}")
    print(f"⌨️  Controls: Press 'q' to quit")
    print("="*60 + "\n")

    # Send ready notification
    try:
        requests.post(BACKEND_URL, json={'type': 'READY', 'camera': f'CAM_{camera_id:02d}', 'location': location}, timeout=1)
        print("[✓] Connected to backend server\n")
    except:
        print("[⚠] Warning: Could not connect to backend. Alerts will not be sent.\n")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("[✗] Failed to read from camera")
            break

        # Process frame and detect falls
        _image, prev_time, fall_detected = detector.handle_frame_with_detection(frame, prev_time)
        
        current_time = time.time()
        
        # If fall just detected, mark the time but don't send yet
        if fall_detected and fall_detected_time is None:
            if (current_time - last_alert_time) >= ALERT_COOLDOWN:
                fall_detected_time = current_time
                print(f"[⚠] Fall detected! Waiting {post_fall_delay}s to capture...")
        
        # If we're waiting for post-fall capture
        if fall_detected_time is not None:
            time_since_detection = current_time - fall_detected_time
            
            # Keep updating the pending frame (capture latest state)
            pending_fall_frame = _image.copy()
            
            # After delay, send the captured frame
            if time_since_detection >= post_fall_delay:
                send_fall_alert_http(pending_fall_frame, f'CAM_{camera_id:02d}', location)
                last_alert_time = current_time
                fall_detected_time = None
                pending_fall_frame = None

        # Show preview
        cv2.imshow("Real-Time Fall Detection - Press 'q' to quit", _image)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            print("\n[✓] Detection stopped by user")
            break

    cap.release()
    cv2.destroyAllWindows()



if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Real-time fall detection with AI')
    parser.add_argument('--camera', type=int, default=0, help='Camera ID (default: 0)')
    parser.add_argument('--location', type=str, default='PHÒNG KHÁCH', help='Camera location name')
    parser.add_argument('--backend', type=str, help='Backend URL (overrides default)')
    args = parser.parse_args()
    
    if args.backend:
        BACKEND_URL = args.backend
    
    try:
        process_realtime_camera(args.camera, args.location)
    except KeyboardInterrupt:
        print("\n[✓] Detection stopped by Ctrl+C")
    except Exception as e:
        print(f"\n[✗] Error: {e}")
