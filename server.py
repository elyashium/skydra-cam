import cv2
import time
import threading
import numpy as np
from flask import Flask, render_template, request, jsonify, Response
from ultralytics import YOLO
import torch
from collections import deque, Counter

# ----------------- CONFIG -----------------
CAMERA_URL = "http://192.168.0.105:8080/video"

# Load YOLOv8 model and force CUDA
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"Loading YOLO model on {device}...")
model = YOLO("yolov8n.pt")
if torch.cuda.is_available():
    model = model.to("cuda")
    print("✅ YOLO model loaded on CUDA")
else:
    print("⚠️ YOLO model loaded on CPU - CUDA not available")

app = Flask(__name__)

# Global variables
latest_gps = {"lat": None, "lon": None}
latest_sensors = {
    "status": "success", 
    "accelerometer": {"available": False},
    "gyroscope": {"available": False},
    "magnetometer": {"available": False},
    "environment": {"light": None, "proximity": None, "battery": None},
}

class CameraProcessor:
    def __init__(self, source=CAMERA_URL):
        self.source = source
        self.cap = None
        self.current_frame = None
        self.display_frame = None  # Frame for web display
        self.frame_count = 0
        
        # FIXED: Persistent detection boxes
        self.current_detections = []  # Store current detection boxes
        self.detection_age = {}  # Track how long each detection has been visible
        self.max_detection_age = 1.5  # Seconds to keep detection visible
        
        # FIXED: Stable detection counting
        self.stable_detection_count = 0  # This is what gets displayed
        self.detection_buffer = deque(maxlen=10)  # Rolling buffer for smoothing
        self.last_detection_update = 0
        
        # Performance metrics
        self.fps = 0
        self.latency_ms = 0
        self.last_fps_time = time.time()
        self.fps_counter = 0
        
        # Threading
        self.running = False
        self.thread = None
        self.frame_lock = threading.Lock()
        
        self.init_camera()
    
    def init_camera(self):
        """Initialize camera with optimal settings"""
        try:
            if self.cap:
                self.cap.release()
            
            print(f"📡 Connecting to camera: {self.source}")
            
            # Use FFMPEG backend for better streaming performance
            self.cap = cv2.VideoCapture(self.source, cv2.CAP_FFMPEG)
            
            if self.cap.isOpened():
                # CRITICAL: Optimize for real-time streaming
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimal buffer
                self.cap.set(cv2.CAP_PROP_FPS, 30)
                
                # Test frame
                ret, test_frame = self.cap.read()
                if ret:
                    print(f"✅ Camera connected: {test_frame.shape}")
                    return True
                else:
                    print("❌ Cannot read frames")
                    return False
            else:
                print("❌ Cannot open camera")
                return False
                
        except Exception as e:
            print(f"❌ Camera error: {e}")
            return False
    
    def start_processing(self):
        """Start processing with high priority"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._process_frames, daemon=True)
            self.thread.start()
            print("🚀 Camera processing started")
    
    def _update_detection_count(self, current_detections):
        """FIXED: Proper detection smoothing without blinking"""
        current_time = time.time()
        
        # Add current detection count to buffer
        self.detection_buffer.append(current_detections)
        
        # Update stable count every 500ms to prevent rapid changes
        if current_time - self.last_detection_update > 0.5:  # 500ms minimum update interval
            if len(self.detection_buffer) >= 3:
                # Use median of recent detections for stability
                recent_detections = list(self.detection_buffer)
                # Get most common detection count
                count_frequency = Counter(recent_detections)
                most_common_count = count_frequency.most_common(1)[0][0]
                
                # Only update if there's a significant change or it's been stable
                if (abs(most_common_count - self.stable_detection_count) >= 1 or
                    recent_detections.count(most_common_count) >= 5):
                    self.stable_detection_count = most_common_count
                    self.last_detection_update = current_time
                    print(f"🔄 Detection count updated: {self.stable_detection_count}")

    def _update_persistent_detections(self, new_detections):
        """Update detection boxes with persistence and aging"""
        current_time = time.time()
        
        if new_detections:  # New inference results available
            # Clear old detections and add new ones
            self.current_detections = []
            self.detection_age = {}
            
            for detection in new_detections:
                detection_id = len(self.current_detections)  # Simple ID based on order
                self.current_detections.append(detection)
                self.detection_age[detection_id] = current_time
        
        # Age out old detections
        expired_ids = []
        for detection_id, timestamp in self.detection_age.items():
            if current_time - timestamp > self.max_detection_age:
                expired_ids.append(detection_id)
        
        # Remove expired detections
        for expired_id in sorted(expired_ids, reverse=True):
            if expired_id < len(self.current_detections):
                del self.current_detections[expired_id]
            del self.detection_age[expired_id]
    
    def _draw_persistent_detections(self, frame):
        """Draw all current persistent detections on frame"""
        current_time = time.time()
        
        for i, detection in enumerate(self.current_detections):
            # Get detection age for alpha blending
            age = current_time - self.detection_age.get(i, current_time)
            alpha = max(0.3, 1.0 - (age / self.max_detection_age))  # Fade out over time
            
            x1, y1, x2, y2, conf, label = detection
            
            # Create color with alpha
            base_color = (0, 255, 0)
            color = tuple(int(c * alpha) for c in base_color)
            
            # Draw detection box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Draw label with background
            label_text = f"{label} {conf:.2f}"
            label_size = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            
            # Label background with alpha
            overlay = frame.copy()
            cv2.rectangle(overlay, (x1, y1-label_size[1]-10), (x1+label_size[0], y1), color, -1)
            cv2.addWeighted(overlay, alpha, frame, 1-alpha, 0, frame)
            
            # Label text
            cv2.putText(frame, label_text, (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
    
    def _process_frames(self):
        """OPTIMIZED: Main processing loop with persistent detections"""
        frame_skip_counter = 0
        last_inference_time = 0
        
        while self.running:
            if not self.cap or not self.cap.isOpened():
                if not self.init_camera():
                    time.sleep(1)
                    continue
            
            # Read frame with timeout handling
            start_read = time.time()
            ret, frame = self.cap.read()
            read_time = time.time() - start_read
            
            if not ret or frame is None:
                print("⚠️ Frame read failed")
                time.sleep(0.1)
                continue
            
            # PERFORMANCE: Skip frames if reading is slow
            if read_time > 0.1:  # If frame read took more than 100ms
                frame_skip_counter += 1
                if frame_skip_counter < 3:  # Skip up to 2 frames
                    continue
                frame_skip_counter = 0
            
            try:
                current_time = time.time()
                
                # OPTIMIZED: Run inference only every 3rd frame and not more than 2 times per second
                should_run_inference = (
                    self.frame_count % 3 == 0 and 
                    current_time - last_inference_time > 0.5  # Max 2 inferences per second
                )
                
                new_detections = []
                
                if should_run_inference:
                    inference_start = time.time()
                    
                    # Resize frame for faster inference
                    height, width = frame.shape[:2]
                    if width > 640:
                        scale = 640 / width
                        new_width = int(width * scale)
                        new_height = int(height * scale)
                        inference_frame = cv2.resize(frame, (new_width, new_height))
                        scale_back = width / 640
                    else:
                        inference_frame = frame
                        scale_back = 1.0
                    
                    # Run YOLO inference
                    results = model.predict(
                        inference_frame, 
                        imgsz=640, 
                        device=device, 
                        verbose=False, 
                        classes=[0],  # Only persons
                        conf=0.5      # Higher confidence threshold for stability
                    )
                    
                    self.latency_ms = round((time.time() - inference_start) * 1000, 1)
                    last_inference_time = current_time
                    
                    # Process detections
                    frame_detections = 0
                    if results[0].boxes is not None:
                        boxes = results[0].boxes
                        
                        for box in boxes:
                            frame_detections += 1
                            
                            # Scale coordinates back to original frame size
                            x1, y1, x2, y2 = box.xyxy[0].tolist()
                            if scale_back != 1.0:
                                x1, y1, x2, y2 = [int(coord * scale_back) for coord in [x1, y1, x2, y2]]
                            else:
                                x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
                            
                            conf = float(box.conf[0])
                            
                            # Store detection for persistent display
                            new_detections.append((x1, y1, x2, y2, conf, "PERSON"))
                    
                    # Update persistent detections with new results
                    self._update_persistent_detections(new_detections)
                    
                    # Update detection count smoothly
                    self._update_detection_count(frame_detections)
                else:
                    # No new inference, just age existing detections
                    self._update_persistent_detections(None)
                
                # ALWAYS draw persistent detections on every frame
                self._draw_persistent_detections(frame)
                
                # Calculate FPS more accurately
                self.fps_counter += 1
                if current_time - self.last_fps_time >= 2.0:  # Update every 2 seconds
                    self.fps = self.fps_counter / (current_time - self.last_fps_time)
                    self.fps_counter = 0
                    self.last_fps_time = current_time
                
                # Add overlay with STABLE detection count
                info_text = [
                    f"FPS: {self.fps:.1f}",
                    f"PERSONS: {len(self.current_detections)}",  # Use current visible detections
                    f"LATENCY: {self.latency_ms}ms",
                    f"DEVICE: {device.upper()}"
                ]
                
                overlay = frame.copy()
                for i, text in enumerate(info_text):
                    y_pos = 30 + (i * 25)
                    cv2.rectangle(overlay, (10, y_pos-20), (200, y_pos+5), (0, 0, 0), -1)
                    cv2.putText(overlay, text, (15, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                # Blend overlay for better visibility
                frame = cv2.addWeighted(frame, 0.8, overlay, 0.2, 0)
                
                # Thread-safe frame update
                with self.frame_lock:
                    self.current_frame = frame.copy()
                
                self.frame_count += 1
                
            except Exception as e:
                print(f"🚨 Processing error: {e}")
                # Keep the last good frame instead of creating error frames
                continue
            
            # CRITICAL: Proper frame rate limiting
            time.sleep(0.033)  # ~30 FPS max
    
    def get_frame_as_jpeg(self):
        """Thread-safe frame retrieval with better compression"""
        with self.frame_lock:
            if self.current_frame is not None:
                try:
                    # Use better JPEG settings for smooth streaming
                    encode_params = [
                        cv2.IMWRITE_JPEG_QUALITY, 80,  # Good quality vs speed balance
                        cv2.IMWRITE_JPEG_OPTIMIZE, 1   # Better compression
                    ]
                    ret, buffer = cv2.imencode('.jpg', self.current_frame, encode_params)
                    if ret:
                        return buffer.tobytes()
                except Exception as e:
                    print(f"JPEG encoding error: {e}")
        
        # Return black frame with connection message
        black_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(black_frame, "CONNECTING TO CAMERA...", (150, 240), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        ret, buffer = cv2.imencode('.jpg', black_frame)
        return buffer.tobytes() if ret else b''
    
    def get_stats(self):
        """Get stable detection statistics"""
        return {
            "detections": len(self.current_detections),  # Use current visible detections
            "fps": round(self.fps, 1),
            "latency": self.latency_ms,
            "status": "active" if self.current_frame is not None else "connecting"
        }
    
    def stop(self):
        """Clean shutdown"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        if self.cap:
            self.cap.release()

# Initialize camera
print("🎥 Initializing camera processor...")
camera = CameraProcessor(CAMERA_URL)

def generate_video_stream():
    """OPTIMIZED: Video stream generation"""
    while True:
        try:
            frame_data = camera.get_frame_as_jpeg()
            if frame_data and len(frame_data) > 0:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n'
                       b'Content-Length: ' + str(len(frame_data)).encode() + b'\r\n\r\n' + 
                       frame_data + b'\r\n')
            time.sleep(0.03)  # ~33ms = 30 FPS
        except Exception as e:
            print(f"Stream error: {e}")
            time.sleep(0.1)

# ----------------- ROUTES -----------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/video_feed")
def video_feed():
    """Optimized video streaming"""
    response = Response(
        generate_video_stream(),
        mimetype='multipart/x-mixed-replace; boundary=frame',
        headers={
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0',
            'Connection': 'close'
        }
    )
    return response

@app.route("/api/detection_stats")
def detection_stats():
    return jsonify(camera.get_stats())

@app.route("/api/gps_data")  
def gps_data():
    return jsonify(latest_gps)

@app.route("/api/sensors")
def sensors_data():
    return jsonify(latest_sensors)

@app.route("/update_location", methods=["POST"])
def update_location():
    global latest_gps
    data = request.json
    if data and "latitude" in data and "longitude" in data:
        latest_gps = {"lat": data["latitude"], "lon": data["longitude"]}
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    print("="*60)
    print("🚀 SKYDRA CAM - PERSISTENT DETECTION BOXES")
    print("="*60)
    print(f"📹 Camera: {CAMERA_URL}")
    print(f"🤖 Device: {device}")
    print(f"🌐 Server: http://localhost:5000")
    print("="*60)
    
    camera.start_processing()
    
    try:
        # Run with optimized settings
        app.run(
            host="0.0.0.0", 
            port=5000, 
            debug=False, 
            threaded=True,
            use_reloader=False  # Prevent double initialization
        )
    finally:
        print("🛑 Shutting down...")
        camera.stop()