"""
Vehicle-Only Detection System for Raspberry Pi 5
Uses YOLOv8 nano for real-time vehicle detection (Car, Motorcycle, Bus, Truck)
"""

import cv2
import numpy as np
from ultralytics import YOLO
import argparse
import time
from collections import defaultdict
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid
from models import Base, LiveDetection
from telegram_service import TelegramService

load_dotenv()

# Vehicle-only classes from COCO dataset
VEHICLE_CLASSES = {
    2: 'car',
    3: 'motorcycle',
    5: 'bus',
    7: 'truck'
}

# Colors for each vehicle class (BGR format for OpenCV)
CLASS_COLORS = {
    'car': (0, 255, 0),        # Green
    'motorcycle': (255, 0, 255),  # Magenta
    'bus': (0, 255, 255),      # Yellow
    'truck': (0, 0, 255)       # Red
}

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///vehical_detections.db')
engine = None
SessionLocal = None

def init_db():
    """Initialize database connection and create tables"""
    global engine, SessionLocal
    try:
        if 'sqlite' in DATABASE_URL:
            engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
        else:
            engine = create_engine(DATABASE_URL, pool_size=20, max_overflow=10)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base.metadata.create_all(bind=engine)
        print(f"[INFO] Database initialized: {DATABASE_URL}")
    except Exception as e:
        print(f"[ERROR] Database initialization failed: {e}")
        engine = None
        SessionLocal = None

def save_detection_to_db(vehicle_counts, total_vehicles, conf_threshold, processing_time):
    """Save detection results to live_detections table"""
    if not SessionLocal:
        print("[ERROR] SessionLocal is None")
        return None
    
    session = None
    try:
        session = SessionLocal()
        report_id = str(uuid.uuid4())[:8]
        
        breakdown_text = "\n".join([f"{k.capitalize()}: {v}" for k, v in vehicle_counts.items()])
        stats = {k: v for k, v in vehicle_counts.items()}
        
        print(f"[DEBUG] Creating detection with report_id={report_id}, vehicles={total_vehicles}")
        
        detection = LiveDetection(
            report_id=report_id,
            timestamp=datetime.now(),
            session_start=datetime.now(),
            session_end=datetime.now(),
            total_detections=total_vehicles,
            confidence_threshold=conf_threshold,
            stats=stats,
            breakdown=breakdown_text
        )
        
        session.add(detection)
        session.commit()
        print(f"[INFO] Detection saved to live_detections: report_id={report_id}, vehicles={total_vehicles}")
        session.close()
        return report_id
    except Exception as e:
        print(f"[ERROR] Failed to save detection: {e}")
        import traceback
        traceback.print_exc()
        if session:
            session.close()
        return None


class VehicleDetector:
    def __init__(self, model_path='yolov8n.pt', conf_threshold=0.4, iou_threshold=0.5, 
                 use_onnx=False, input_size=640, enable_enhancement=True, enable_tracking=True):
        """
        Initialize Vehicle Detector
        
        Args:
            model_path: Path to YOLO model
            conf_threshold: Confidence threshold for detections
            iou_threshold: IoU threshold for NMS
            use_onnx: Use ONNX runtime for faster inference
            input_size: Input size for model (larger = better accuracy)
            enable_enhancement: Enable image preprocessing for better quality
            enable_tracking: Enable vehicle tracking with ByteTrack (assigns unique IDs)
        """
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.input_size = input_size
        self.enable_enhancement = enable_enhancement
        self.enable_tracking = enable_tracking
        self.vehicle_counts = defaultdict(int)
        self.total_vehicles = 0
        
        # Tracking state
        self.active_tracks = {}  # {track_id: {'box': ..., 'class_name': ..., 'conf': ..., 'class_id': ...}}
        self.next_track_id = 1
        self.track_history = defaultdict(list)  # {track_id: [(cx, cy), ...]} for trail drawing
        self.max_trail_length = 30  # Max frames of trail to keep
        self.total_unique_vehicles = 0  # Total unique vehicles seen across all frames
        
        # Counting line state
        self.counting_line = None  # ((x1,y1), (x2,y2)) - line coordinates
        self.counting_line_enabled = False
        self.counted_track_ids = set()  # Track IDs that have already crossed the line
        self.line_crossing_counts = defaultdict(int)  # {class_name: count} for line crossings
        self.total_line_crossings = 0  # Total vehicles that crossed the line
        self.counting_direction = 'both'  # 'up', 'down', or 'both'
        
        # Speed estimation state
        self.speed_estimation_enabled = True
        self.pixels_per_meter = 10.0  # Calibration: pixels = meters * pixels_per_meter (default 10px = 1m)
        self.track_speeds = {}  # {track_id: current_speed_kmh}
        self.track_speed_history = defaultdict(list)  # {track_id: [speed1, speed2, ...]} for smoothing
        
        # Alert system state
        self.alert_system_enabled = True
        self.speed_threshold = 60.0  # km/h - alert if vehicle exceeds this speed
        self.vehicle_count_threshold = 5  # alert if more than this many vehicles in frame
        self.alert_callbacks = []  # List of callback functions for alerts
        self.active_alerts = set()  # Track IDs that are currently in alert state
        self.alert_cooldown = 30  # Frames before same alert can trigger again
        self.alert_cooldowns = {}  # {alert_key: frame_count}
        
        # Heatmap state
        self.heatmap_enabled = False
        self.heatmap_accumulator = None  # 2D array to accumulate vehicle positions
        self.heatmap_frame_size = None  # (width, height) of the heatmap
        self.heatmap_alpha = 0.6  # Transparency of heatmap overlay
        self.heatmap_colormap = cv2.COLORMAP_JET  # Color map for heatmap
        
        # Color detection state
        self.color_detection_enabled = False
        self.color_confidence_threshold = 0.5  # Minimum confidence for color detection
        
        # Traffic violation detection state
        self.violation_detection_enabled = False
        self.speed_limit = 60.0  # km/h - default speed limit for violation detection
        self.violation_callbacks = []  # List of callback functions for violations
        self.detected_violations = []  # List of detected violations
        
        # Wrong-way detection state
        self.wrong_way_detection_enabled = False
        self.forbidden_direction = None  # (dx, dy) normalized vector or 'up', 'down', 'left', 'right'
        
        # Blacklist/Whitelist state
        self.blacklist_plates = set()
        self.whitelist_plates = set()
        
        # Telegram service
        self.telegram_service = TelegramService()
        self.telegram_alerts_enabled = True
        
        # Load model
        print(f"[INFO] Loading model: {model_path}")
        self.model = YOLO(model_path)
        
        # Warm up model
        print("[INFO] Warming up model...")
        dummy_input = np.zeros((input_size, input_size, 3), dtype=np.uint8)
        self.model.predict(dummy_input, verbose=False)
        print("[INFO] Model ready!")
        if self.enable_tracking:
            print("[INFO] Vehicle tracking enabled (ByteTrack)")
    
    def enhance_image(self, frame):
        """
        Enhance image quality for better detection
        - Denoising to reduce blur
        - Sharpening to enhance edges
        - Contrast enhancement using CLAHE
        
        Args:
            frame: Input frame (BGR image)
            
        Returns:
            Enhanced frame
        """
        if not self.enable_enhancement:
            return frame
        
        # Denoising - reduces noise while preserving edges
        denoised = cv2.fastNlMeansDenoisingColored(frame, None, 10, 10, 7, 21)
        
        # Sharpening using kernel
        sharpen_kernel = np.array([[-1, -1, -1],
                                   [-1,  9, -1],
                                   [-1, -1, -1]])
        sharpened = cv2.filter2D(denoised, -1, sharpen_kernel)
        
        # Contrast enhancement using CLAHE (Contrast Limited Adaptive Histogram Equalization)
        lab = cv2.cvtColor(sharpened, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        return enhanced
    
    def filter_vehicle_detections(self, results):
        """
        Filter detections to keep only vehicle classes, including track IDs if tracking is enabled
        
        Args:
            results: YOLO detection results (from predict or track)
            
        Returns:
            List of filtered detections with optional track_id
        """
        filtered_detections = []
        
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
                
            for box in boxes:
                class_id = int(box.cls.item())
                conf = float(box.conf.item())
                
                # Only keep vehicle classes
                if class_id in VEHICLE_CLASSES and conf >= self.conf_threshold:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    class_name = VEHICLE_CLASSES[class_id]
                    
                    detection = {
                        'box': (int(x1), int(y1), int(x2), int(y2)),
                        'class_id': class_id,
                        'conf': conf,
                        'class_name': class_name,
                        'track_id': None
                    }
                    
                    # Extract track ID if tracking is enabled
                    if self.enable_tracking and hasattr(box, 'id') and box.id is not None:
                        track_id = int(box.id.item())
                        detection['track_id'] = track_id
                    
                    filtered_detections.append(detection)
        
        return filtered_detections
    
    def draw_detections(self, frame, detections):
        """
        Draw bounding boxes, labels, and tracking trails for vehicle detections
        
        Args:
            frame: Input frame
            detections: List of detection dictionaries
            
        Returns:
            Frame with drawn detections
        """
        for det in detections:
            x1, y1, x2, y2 = det['box']
            class_name = det['class_name']
            conf = det['conf']
            track_id = det.get('track_id')
            color = CLASS_COLORS.get(class_name, (0, 255, 0))
            
            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Prepare label (include track ID and speed if available)
            speed = None
            if track_id is not None and track_id in self.track_speeds:
                speed = self.track_speeds[track_id]
            
            if track_id is not None and speed is not None:
                label = f"ID:{track_id} {class_name}: {conf:.2f} | {speed:.1f} km/h"
            elif track_id is not None:
                label = f"ID:{track_id} {class_name}: {conf:.2f}"
            else:
                label = f"{class_name}: {conf:.2f}"
            
            # Draw label background
            (label_w, label_h), _ = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2
            )
            cv2.rectangle(
                frame, 
                (x1, y1 - label_h - 10), 
                (x1 + label_w, y1), 
                color, 
                -1
            )
            
            # Draw label text
            cv2.putText(
                frame, label, (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2
            )
            
            # Draw speed label if available
            if 'speed' in det and det['speed'] is not None:
                speed_label = f"{det['speed']:.1f} km/h"
                cv2.putText(frame, speed_label, (x1, y1 - 10),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
            
            # Draw color label if available
            if 'color' in det and det['color'] != 'unknown':
                color_label = f"Color: {det['color']}"
                cv2.putText(frame, color_label, (x1, y2 + 20),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            
            # Draw tracking trail if track ID is available
            if track_id is not None and track_id in self.track_history:
                trail = self.track_history[track_id]
                if len(trail) > 1:
                    for i in range(1, len(trail)):
                        # Fade trail: older points are thinner
                        thickness = max(1, int(i * 2 / len(trail)))
                        cv2.line(frame, trail[i - 1], trail[i], color, thickness)
        
        return frame
    
    def update_counts(self, detections):
        """Update vehicle counts and tracking state"""
        current_frame_counts = defaultdict(int)
        new_tracks_this_frame = set()
        
        for det in detections:
            class_name = det['class_name']
            track_id = det.get('track_id')
            current_frame_counts[class_name] += 1
            
            # Update tracking state
            if track_id is not None:
                # Update active tracks
                self.active_tracks[track_id] = {
                    'box': det['box'],
                    'class_name': class_name,
                    'conf': det['conf'],
                    'class_id': det['class_id']
                }
                
                # Update trail history (center point)
                x1, y1, x2, y2 = det['box']
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                self.track_history[track_id].append((cx, cy))
                
                # Limit trail length
                if len(self.track_history[track_id]) > self.max_trail_length:
                    self.track_history[track_id] = self.track_history[track_id][-self.max_trail_length:]
                
                new_tracks_this_frame.add(track_id)
        
        # Count new unique vehicles (track IDs we haven't seen before)
        if self.enable_tracking:
            for track_id in new_tracks_this_frame:
                if track_id not in self._seen_track_ids if hasattr(self, '_seen_track_ids') else True:
                    if not hasattr(self, '_seen_track_ids'):
                        self._seen_track_ids = set()
                    if track_id not in self._seen_track_ids:
                        self._seen_track_ids.add(track_id)
                        self.total_unique_vehicles += 1
        
        self.vehicle_counts = current_frame_counts
        self.total_vehicles = sum(current_frame_counts.values())
        
        return current_frame_counts
    
    def draw_stats(self, frame, fps):
        """Draw FPS and vehicle count statistics on frame"""
        # Draw FPS
        cv2.putText(
            frame, f"FPS: {fps:.1f}", (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2
        )
        
        # Draw vehicle counts
        y_offset = 60
        cv2.putText(
            frame, f"Total Vehicles: {self.total_vehicles}", (10, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2
        )
        
        # Show unique vehicle count if tracking is enabled
        if self.enable_tracking and self.total_unique_vehicles > 0:
            y_offset += 25
            cv2.putText(
                frame, f"Unique Tracked: {self.total_unique_vehicles}", (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2
            )
        
        y_offset += 25
        for class_name, count in self.vehicle_counts.items():
            color = CLASS_COLORS.get(class_name, (255, 255, 255))
            cv2.putText(
                frame, f"  {class_name}: {count}", (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1
            )
            y_offset += 20
        
        return frame
    
    def enable_heatmap(self, frame_size=None, alpha=0.6, colormap=cv2.COLORMAP_JET):
        """
        Enable heatmap visualization for traffic density
        
        Args:
            frame_size: (width, height) of the video frame (will be set from first frame if None)
            alpha: Transparency of heatmap overlay (0.0-1.0)
            colormap: OpenCV colormap constant (default: cv2.COLORMAP_JET)
        """
        self.heatmap_enabled = True
        self.heatmap_alpha = max(0.0, min(1.0, alpha))
        self.heatmap_colormap = colormap
        
        if frame_size is not None:
            self.heatmap_frame_size = frame_size
            self.heatmap_accumulator = np.zeros((frame_size[1], frame_size[0]), dtype=np.float32)
        
        print(f"[INFO] Heatmap enabled (alpha: {self.heatmap_alpha}, colormap: {colormap})")
    
    def disable_heatmap(self):
        """Disable heatmap visualization"""
        self.heatmap_enabled = False
        self.heatmap_accumulator = None
        print("[INFO] Heatmap disabled")
    
    def clear_heatmap(self):
        """Clear accumulated heatmap data"""
        if self.heatmap_accumulator is not None:
            self.heatmap_accumulator.fill(0)
        print("[INFO] Heatmap cleared")
    
    def update_heatmap(self, detections, frame_size):
        """
        Update heatmap accumulator with vehicle positions
        
        Args:
            detections: List of detection dictionaries
            frame_size: (width, height) of the current frame
        """
        if not self.heatmap_enabled:
            return
        
        # Initialize accumulator on first frame
        if self.heatmap_accumulator is None:
            self.heatmap_frame_size = frame_size
            self.heatmap_accumulator = np.zeros((frame_size[1], frame_size[0]), dtype=np.float32)
        
        # Resize accumulator if frame size changed
        if self.heatmap_accumulator.shape != (frame_size[1], frame_size[0]):
            self.heatmap_accumulator = np.zeros((frame_size[1], frame_size[0]), dtype=np.float32)
            self.heatmap_frame_size = frame_size
        
        # Add vehicle positions to heatmap
        for det in detections:
            x1, y1, x2, y2 = det['box']
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            
            # Add a small circle around each vehicle center
            radius = 20
            cv2.circle(self.heatmap_accumulator, (center_x, center_y), radius, 1.0, -1)
    
    def draw_heatmap(self, frame):
        """
        Draw heatmap overlay on the frame
        
        Args:
            frame: Input frame
            
        Returns:
            Frame with heatmap overlay
        """
        if not self.heatmap_enabled or self.heatmap_accumulator is None:
            return frame
        
        # Normalize heatmap to 0-255
        heatmap_normalized = np.zeros_like(self.heatmap_accumulator)
        if self.heatmap_accumulator.max() > 0:
            heatmap_normalized = (self.heatmap_accumulator / self.heatmap_accumulator.max() * 255).astype(np.uint8)
        
        # Apply colormap
        heatmap_colored = cv2.applyColorMap(heatmap_normalized, self.heatmap_colormap)
        
        # Resize heatmap to match frame if needed
        if heatmap_colored.shape[:2] != frame.shape[:2]:
            heatmap_colored = cv2.resize(heatmap_colored, (frame.shape[1], frame.shape[0]))
        
        # Blend with original frame
        result = cv2.addWeighted(frame, 1 - self.heatmap_alpha, heatmap_colored, self.heatmap_alpha, 0)
        
        return result
    
    def enable_color_detection(self, confidence_threshold=0.5):
        """
        Enable vehicle color detection
        
        Args:
            confidence_threshold: Minimum confidence for color detection (0.0-1.0)
        """
        self.color_detection_enabled = True
        self.color_confidence_threshold = max(0.0, min(1.0, confidence_threshold))
        print(f"[INFO] Color detection enabled (confidence threshold: {self.color_confidence_threshold})")
    
    def disable_color_detection(self):
        """Disable color detection"""
        self.color_detection_enabled = False
        print("[INFO] Color detection disabled")
    
    def detect_color(self, frame, bbox):
        """
        Detect the dominant color of a vehicle from its bounding box
        
        Args:
            frame: Input frame (BGR)
            bbox: Bounding box (x1, y1, x2, y2)
            
        Returns:
            Detected color name and confidence
        """
        x1, y1, x2, y2 = bbox
        
        # Extract vehicle region
        vehicle_region = frame[y1:y2, x1:x2]
        if vehicle_region.size == 0:
            return 'unknown', 0.0
        
        # Convert to HSV color space
        hsv = cv2.cvtColor(vehicle_region, cv2.COLOR_BGR2HSV)
        
        # Define color ranges in HSV
        color_ranges = {
            'white': ([0, 0, 200], [180, 30, 255]),
            'black': ([0, 0, 0], [180, 255, 50]),
            'red': ([0, 100, 100], [10, 255, 255]),
            'red2': ([170, 100, 100], [180, 255, 255]),  # Red wraps around
            'green': ([40, 50, 50], [80, 255, 255]),
            'blue': ([100, 50, 50], [130, 255, 255]),
            'yellow': ([20, 100, 100], [40, 255, 255]),
            'gray': ([0, 0, 50], [180, 30, 200]),
            'silver': ([0, 0, 150], [180, 15, 220]),
        }
        
        # Count pixels in each color range
        color_counts = {}
        for color_name, (lower, upper) in color_ranges.items():
            lower = np.array(lower, dtype=np.uint8)
            upper = np.array(upper, dtype=np.uint8)
            mask = cv2.inRange(hsv, lower, upper)
            count = cv2.countNonZero(mask)
            
            # Combine red ranges
            if color_name == 'red2':
                color_counts['red'] = color_counts.get('red', 0) + count
            elif color_name != 'red2':
                color_counts[color_name] = count
        
        # Find dominant color
        if not color_counts:
            return 'unknown', 0.0
        
        total_pixels = sum(color_counts.values())
        if total_pixels == 0:
            return 'unknown', 0.0
        
        dominant_color = max(color_counts, key=color_counts.get)
        confidence = color_counts[dominant_color] / total_pixels
        
        # Map similar colors
        if dominant_color == 'silver' and confidence < 0.3:
            dominant_color = 'gray'
        
        return dominant_color, confidence
    
    def enable_violation_detection(self, speed_limit=60.0):
        """
        Enable traffic violation detection
        
        Args:
            speed_limit: Speed limit in km/h for violation detection
        """
        self.violation_detection_enabled = True
        self.speed_limit = speed_limit
        print(f"[INFO] Violation detection enabled (speed limit: {speed_limit} km/h)")
    
    def disable_violation_detection(self):
        """Disable violation detection"""
        self.violation_detection_enabled = False
        print("[INFO] Violation detection disabled")
    
    def add_violation_callback(self, callback):
        """
        Add a callback function for violation notifications
        
        Args:
            callback: Function that accepts violation data dict
        """
        self.violation_callbacks.append(callback)
        print(f"[INFO] Violation callback added (total: {len(self.violation_callbacks)})")
    
    def detect_violations(self, detections):
        """
        Detect traffic violations from detections
        
        Args:
            detections: List of detection dictionaries
            
        Returns:
            List of detected violations
        """
        if not self.violation_detection_enabled:
            return []
        
        violations = []
        
        # Check for speed violations
        if self.speed_estimation_enabled and self.enable_tracking:
            for det in detections:
                track_id = det.get('track_id')
                if track_id is not None and track_id in self.track_speeds:
                    speed = self.track_speeds[track_id]
                    if speed > self.speed_limit:
                        violation = {
                            'type': 'speeding',
                            'track_id': track_id,
                            'speed': speed,
                            'speed_limit': self.speed_limit,
                            'excess': speed - self.speed_limit,
                            'class_name': det['class_name'],
                            'box': det['box'],
                            'timestamp': datetime.now().isoformat()
                        }
                        violations.append(violation)
        
        # Trigger callbacks for all violations
        for violation in violations:
            self.detected_violations.append(violation)
            for callback in self.violation_callbacks:
                try:
                    callback(violation)
                except Exception as e:
                    print(f"[ERROR] Violation callback error: {e}")
        
        return violations
    
    def calculate_speed(self, track_id, fps):
        """
        Calculate speed for a tracked vehicle based on position history
        
        Args:
            track_id: ID of the track
            fps: Current video frame rate
            
        Returns:
            Speed in km/h (or None if insufficient data)
        """
        if track_id not in self.track_history or len(self.track_history[track_id]) < 2:
            return None
        
        trail = self.track_history[track_id]
        
        # Use the last 2 positions for instantaneous speed
        prev_pos = trail[-2]
        curr_pos = trail[-1]
        
        # Calculate pixel distance
        pixel_distance = np.sqrt((curr_pos[0] - prev_pos[0])**2 + (curr_pos[1] - prev_pos[1])**2)
        
        # Convert to meters
        distance_meters = pixel_distance / self.pixels_per_meter
        
        # Convert to km/h (distance in meters / time in seconds * 3.6)
        if fps > 0:
            speed_ms = distance_meters / (1.0 / fps)  # meters per second
            speed_kmh = speed_ms * 3.6
            return speed_kmh
        
        return None
    
    def update_speeds(self, detections, fps):
        """
        Update speed estimates for all tracked vehicles
        
        Args:
            detections: List of detection dictionaries
            fps: Current video frame rate
        """
        if not self.speed_estimation_enabled or not self.enable_tracking:
            return
        
        for det in detections:
            track_id = det.get('track_id')
            if track_id is None:
                continue
            
            speed = self.calculate_speed(track_id, fps)
            if speed is not None:
                # Smooth speed using moving average
                self.track_speed_history[track_id].append(speed)
                if len(self.track_speed_history[track_id]) > 5:  # Keep last 5 values
                    self.track_speed_history[track_id] = self.track_speed_history[track_id][-5:]
                
                # Calculate average speed
                avg_speed = sum(self.track_speed_history[track_id]) / len(self.track_speed_history[track_id])
                self.track_speeds[track_id] = avg_speed
    
    def set_speed_calibration(self, pixels_per_meter):
        """
        Set calibration for speed estimation (pixels per meter)
        
        Args:
            pixels_per_meter: Number of pixels that equal 1 meter in the video
        """
        self.pixels_per_meter = max(0.1, pixels_per_meter)
        print(f"[INFO] Speed calibration set: {self.pixels_per_meter} pixels/meter")
    
    def set_speed_threshold(self, threshold_kmh):
        """
        Set speed threshold for alerts
        
        Args:
            threshold_kmh: Speed in km/h that triggers alert
        """
        self.speed_threshold = threshold_kmh
        print(f"[INFO] Speed alert threshold set: {threshold_kmh} km/h")
    
    def set_vehicle_count_threshold(self, threshold):
        """
        Set vehicle count threshold for alerts
        
        Args:
            threshold: Number of vehicles that triggers alert
        """
        self.vehicle_count_threshold = threshold
        print(f"[INFO] Vehicle count alert threshold set: {threshold}")
    
    def add_alert_callback(self, callback):
        """
        Add a callback function that gets called when an alert triggers
        
        Args:
            callback: Function that accepts (alert_type, data) dict
        """
        self.alert_callbacks.append(callback)
        print(f"[INFO] Alert callback added (total: {len(self.alert_callbacks)})")
    
    def check_alerts(self, detections):
        """
        Check if any alert conditions are met and trigger callbacks
        
        Args:
            detections: List of detection dictionaries
            
        Returns:
            List of triggered alerts
        """
        if not self.alert_system_enabled:
            return []
        
        triggered_alerts = []
        
        # Check speed threshold for each tracked vehicle
        if self.speed_estimation_enabled and self.enable_tracking:
            for det in detections:
                track_id = det.get('track_id')
                if track_id is not None and track_id in self.track_speeds:
                    speed = self.track_speeds[track_id]
                    if speed > self.speed_threshold:
                        alert_key = f"speed_{track_id}"
                        if alert_key not in self.alert_cooldowns or self.alert_cooldowns[alert_key] <= 0:
                            alert_data = {
                                'type': 'speed_exceeded',
                                'track_id': track_id,
                                'speed': speed,
                                'threshold': self.speed_threshold,
                                'class_name': det['class_name'],
                                'box': det['box']
                            }
                            triggered_alerts.append(alert_data)
                            self.alert_cooldowns[alert_key] = self.alert_cooldown
                            self.active_alerts.add(track_id)
        
        # Check vehicle count threshold
        vehicle_count = len(detections)
        if vehicle_count > self.vehicle_count_threshold:
            alert_key = "count_exceeded"
            if alert_key not in self.alert_cooldowns or self.alert_cooldowns[alert_key] <= 0:
                alert_data = {
                    'type': 'count_exceeded',
                    'count': vehicle_count,
                    'threshold': self.vehicle_count_threshold,
                    'detections': detections
                }
                triggered_alerts.append(alert_data)
                self.alert_cooldowns[alert_key] = self.alert_cooldown
        
        # Check for wrong-way violations
        if self.wrong_way_detection_enabled and self.enable_tracking:
            wrong_way_vehicles = self.detect_wrong_way(detections)
            for v in wrong_way_vehicles:
                alert_key = f"wrong_way_{v['track_id']}"
                if alert_key not in self.alert_cooldowns or self.alert_cooldowns[alert_key] <= 0:
                    alert_data = {
                        'type': 'wrong_way',
                        'track_id': v['track_id'],
                        'class_name': v['class_name'],
                        'box': v['box'],
                        'direction': 'forbidden'
                    }
                    triggered_alerts.append(alert_data)
                    self.alert_cooldowns[alert_key] = self.alert_cooldown
        
        # Trigger callbacks for all alerts
        for alert in triggered_alerts:
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    print(f"[ERROR] Alert callback error: {e}")
            
            # Send to Telegram if enabled
            if self.telegram_alerts_enabled and self.telegram_service:
                self.telegram_service.send_alert(alert['type'], {
                    'Vehicle': alert.get('class_name', 'Unknown'),
                    'ID': alert.get('track_id', 'N/A'),
                    'Detail': f"{alert.get('speed', '')} km/h" if alert['type'] == 'speed_exceeded' else "Wrong Direction"
                })
        
        # Decrease cooldown counters
        for key in list(self.alert_cooldowns.keys()):
            self.alert_cooldowns[key] -= 1
            if self.alert_cooldowns[key] <= 0:
                del self.alert_cooldowns[key]
        
        # Remove from active alerts if no longer triggering
        if self.speed_estimation_enabled and self.enable_tracking:
            for track_id in list(self.active_alerts):
                if track_id not in self.track_speeds or self.track_speeds[track_id] <= self.speed_threshold:
                    self.active_alerts.discard(track_id)
        
        return triggered_alerts
    
    def set_counting_line(self, point1, point2, direction='both'):
        """
        Set a virtual counting line on the frame
        
        Args:
            point1: (x, y) tuple for first point of the line
            point2: (x, y) tuple for second point of the line
            direction: 'up' (crossing upward), 'down' (crossing downward), or 'both'
        """
        self.counting_line = (point1, point2)
        self.counting_line_enabled = True
        self.counting_direction = direction
        self.counted_track_ids = set()
        self.line_crossing_counts = defaultdict(int)
        self.total_line_crossings = 0
        print(f"[INFO] Counting line set: {point1} -> {point2}, direction: {direction}")
    
    def clear_counting_line(self):
        """Clear the counting line and reset counts"""
        self.counting_line = None
        self.counting_line_enabled = False
        self.counted_track_ids = set()
        self.line_crossing_counts = defaultdict(int)
        self.total_line_crossings = 0
    
    def _segments_intersect(self, p1, p2, p3, p4):
        """
        Check if line segment p1-p2 intersects with segment p3-p4
        
        Args:
            p1, p2: Points of first segment
            p3, p4: Points of second segment
            
        Returns:
            True if segments intersect
        """
        def cross(o, a, b):
            return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
        
        d1 = cross(p3, p4, p1)
        d2 = cross(p3, p4, p2)
        d3 = cross(p1, p2, p3)
        d4 = cross(p1, p2, p4)
        
        if ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and \
           ((d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0)):
            return True
        
        return False
    
    def check_line_crossings(self, detections):
        """
        Check if any tracked vehicles have crossed the counting line
        
        Args:
            detections: List of detection dictionaries with track_ids
            
        Returns:
            List of newly crossed detections
        """
        if not self.counting_line_enabled or not self.enable_tracking:
            return []
        
        newly_crossed = []
        line_p1, line_p2 = self.counting_line
        
        for det in detections:
            track_id = det.get('track_id')
            if track_id is None or track_id in self.counted_track_ids:
                continue
            
            # Check if this track has history (previous position)
            if track_id not in self.track_history or len(self.track_history[track_id]) < 2:
                continue
            
            # Get current and previous center positions
            trail = self.track_history[track_id]
            prev_pos = trail[-2]
            curr_pos = trail[-1]
            
            # Check direction filtering
            if self.counting_direction == 'up' and curr_pos[1] > prev_pos[1]:
                continue  # Moving downward, skip
            elif self.counting_direction == 'down' and curr_pos[1] < prev_pos[1]:
                continue  # Moving upward, skip
            
            # Check if movement segment intersects counting line
            if self._segments_intersect(prev_pos, curr_pos, line_p1, line_p2):
                self.counted_track_ids.add(track_id)
                self.line_crossing_counts[det['class_name']] += 1
                self.total_line_crossings += 1
                newly_crossed.append(det)
        
        return newly_crossed
    
    def draw_counting_line(self, frame):
        """
        Draw the counting line and crossing count on the frame
        
        Args:
            frame: Input frame
            
        Returns:
            Frame with counting line drawn
        """
        if not self.counting_line_enabled or self.counting_line is None:
            return frame
        
        p1, p2 = self.counting_line
        
        # Draw counting line
        line_color = (0, 255, 255)  # Yellow
        thickness = 2
        
        # Draw solid line
        cv2.line(frame, p1, p2, line_color, thickness)
        
        # Draw endpoints
        cv2.circle(frame, p1, 5, line_color, -1)
        cv2.circle(frame, p2, 5, line_color, -1)
        
        # Draw crossing count near the line
        mid_x = (p1[0] + p2[0]) // 2
        mid_y = (p1[1] + p2[1]) // 2
        
        # Background for count text
        count_text = f"Crossed: {self.total_line_crossings}"
        (text_w, text_h), _ = cv2.getTextSize(count_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
        cv2.rectangle(frame, (mid_x - text_w // 2 - 5, mid_y - text_h - 15),
                      (mid_x + text_w // 2 + 5, mid_y - 5), (0, 0, 0), -1)
        cv2.putText(frame, count_text, (mid_x - text_w // 2, mid_y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, line_color, 2)
        
        # Draw per-class counts below the line
        y_off = mid_y + 15
        for class_name, count in self.line_crossing_counts.items():
            color = CLASS_COLORS.get(class_name, (255, 255, 255))
            cv2.putText(frame, f"{class_name}: {count}", (mid_x - 30, y_off),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            y_off += 20
        
        return frame
    
    def set_wrong_way_direction(self, direction='up'):
        """
        Set the forbidden direction for wrong-way detection
        
        Args:
            direction: 'up', 'down', 'left', or 'right'
        """
        self.wrong_way_detection_enabled = True
        self.forbidden_direction = direction
        print(f"[INFO] Wrong-way detection enabled. Forbidden direction: {direction}")

    def detect_wrong_way(self, detections):
        """
        Detect vehicles moving in the forbidden direction
        
        Args:
            detections: List of detection dictionaries
            
        Returns:
            List of vehicles moving the wrong way
        """
        if not self.wrong_way_detection_enabled or not self.enable_tracking:
            return []
            
        wrong_way_vehicles = []
        for det in detections:
            track_id = det.get('track_id')
            if track_id is None or track_id not in self.track_history or len(self.track_history[track_id]) < 5:
                continue
                
            trail = self.track_history[track_id]
            start_pos = trail[0]
            end_pos = trail[-1]
            
            dx = end_pos[0] - start_pos[0]
            dy = end_pos[1] - start_pos[1]
            
            is_wrong = False
            if self.forbidden_direction == 'up' and dy < -20:  # Moving significantly up
                is_wrong = True
            elif self.forbidden_direction == 'down' and dy > 20:  # Moving significantly down
                is_wrong = True
            elif self.forbidden_direction == 'left' and dx < -20:  # Moving significantly left
                is_wrong = True
            elif self.forbidden_direction == 'right' and dx > 20:  # Moving significantly right
                is_wrong = True
                
            if is_wrong:
                wrong_way_vehicles.append(det)
                
        return wrong_way_vehicles

    def detect(self, frame):
        """
        Run detection on a single frame (with tracking if enabled)
        
        Args:
            frame: Input frame (BGR image)
            
        Returns:
            Annotated frame and list of detections
        """
        # Enhance image quality for better detection
        enhanced_frame = self.enhance_image(frame)
        
        # Run inference - use track() if tracking enabled, predict() otherwise
        if self.enable_tracking:
            results = self.model.track(
                enhanced_frame,
                imgsz=self.input_size,
                conf=self.conf_threshold,
                iou=self.iou_threshold,
                verbose=False,
                persist=True,  # Keep tracker state between frames
                tracker="bytetrack.yaml",  # ByteTrack tracker
                classes=list(VEHICLE_CLASSES.keys())
            )
        else:
            results = self.model.predict(
                enhanced_frame,
                imgsz=self.input_size,
                conf=self.conf_threshold,
                iou=self.iou_threshold,
                verbose=False,
                classes=list(VEHICLE_CLASSES.keys())
            )
        
        # Filter detections (includes track IDs if available)
        detections = self.filter_vehicle_detections(results)
        
        # Detect vehicle colors if enabled
        if self.color_detection_enabled:
            for det in detections:
                color, confidence = self.detect_color(frame, det['box'])
                if confidence >= self.color_confidence_threshold:
                    det['color'] = color
                    det['color_confidence'] = confidence
                else:
                    det['color'] = 'unknown'
                    det['color_confidence'] = confidence
        
        # Update counts and tracking state
        self.update_counts(detections)
        
        # Update speed estimates (requires tracking)
        if self.speed_estimation_enabled and self.enable_tracking:
            self.update_speeds(detections, fps=30)  # Default 30 FPS, should be passed from process_video
        
        # Check counting line crossings (requires tracking)
        if self.counting_line_enabled and self.enable_tracking:
            self.check_line_crossings(detections)
        
        # Check alerts (speed/count thresholds)
        if self.alert_system_enabled:
            self.check_alerts(detections)
        
        # Detect traffic violations
        if self.violation_detection_enabled:
            self.detect_violations(detections)
        
        # Draw detections on original frame (not enhanced)
        annotated_frame = self.draw_detections(frame.copy(), detections)
        
        # Draw counting line if enabled
        if self.counting_line_enabled:
            annotated_frame = self.draw_counting_line(annotated_frame)
        
        # Update and draw heatmap if enabled
        if self.heatmap_enabled:
            frame_size = (frame.shape[1], frame.shape[0])
            self.update_heatmap(detections, frame_size)
            annotated_frame = self.draw_heatmap(annotated_frame)
        
        return annotated_frame, detections


def process_video(detector, source, output_path=None, display=True, save_frames=False, custom_width=None, custom_height=None):
    """
    Process video stream (webcam, Raspberry Pi camera, or file)
    
    Args:
        detector: VehicleDetector instance
        source: Video source ('picam' for RPi camera, 0 for webcam, or path to video file)
        output_path: Path to save output video
        display: Whether to display live feed
        save_frames: Whether to save frames with detections
    """
    # Check if using Raspberry Pi Camera Module
    use_picam = (source == 'picam')
    
    if use_picam:
        try:
            from picamera2 import Picamera2
            print("[INFO] Using Raspberry Pi Camera Module (picamera2)")
            picam = Picamera2()
            # Use native resolution or custom resolution if specified
            if custom_width and custom_height:
                config = picam.create_video_configuration(
                    main={"size": (custom_width, custom_height), "format": "RGB888"}
                )
                print(f"[INFO] Using custom resolution: {custom_width}x{custom_height}")
            else:
                # Use camera's native resolution (HD/720p/1080p)
                config = picam.create_video_configuration(
                    main={"format": "RGB888"}
                )
                print("[INFO] Using camera native resolution")
            picam.configure(config)
            picam.start()
            time.sleep(2)  # Warm up camera
            frame_width = config['main']['size'][0]
            frame_height = config['main']['size'][1]
            fps_input = 30
        except ImportError:
            print("[ERROR] picamera2 not installed. Install with: pip install picamera2")
            print("[INFO] Or use --source 0 for USB webcam")
            return
        except Exception as e:
            print(f"[ERROR] Failed to initialize Raspberry Pi camera: {e}")
            return
    else:
        # Open video capture
        if source.isdigit():
            source = int(source)
            cap = cv2.VideoCapture(source)
            # Use custom resolution if specified, otherwise use camera native resolution
            if custom_width and custom_height:
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, custom_width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, custom_height)
                print(f"[INFO] Using custom resolution: {custom_width}x{custom_height}")
            else:
                print("[INFO] Using camera native resolution")
            cap.set(cv2.CAP_PROP_FPS, 30)
        else:
            cap = cv2.VideoCapture(source)
        
        if not cap.isOpened():
            print(f"[ERROR] Cannot open video source: {source}")
            return
        
        # Get video properties
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps_input = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"[INFO] Video resolution: {frame_width}x{frame_height}")
    print(f"[INFO] Input FPS: {fps_input}")
    
    # Initialize database
    init_db()
    
    # Initialize video writer if output path specified
    writer = None
    if output_path:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(output_path, fourcc, 20, (frame_width, frame_height))
        print(f"[INFO] Saving output to: {output_path}")
    
    # FPS calculation variables
    fps = 0
    frame_count = 0
    start_time = time.time()
    
    # Database save timer
    last_db_save = time.time()
    db_save_interval = 30  # Save to DB every 30 seconds
    
    print("[INFO] Starting detection... Press 'q' to quit")
    
    try:
        while True:
            if use_picam:
                frame_rgb = picam.capture_array()
                frame = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
            else:
                ret, frame = cap.read()
                if not ret:
                    print("[INFO] End of video stream")
                    break
            
            # Run detection
            loop_start = time.time()
            annotated_frame, detections = detector.detect(frame)
            inference_time = time.time() - loop_start
            
            # Calculate FPS
            frame_count += 1
            elapsed_time = time.time() - start_time
            if elapsed_time > 1.0:
                fps = frame_count / elapsed_time
                frame_count = 0
                start_time = time.time()
            
            # Draw statistics
            annotated_frame = detector.draw_stats(annotated_frame, fps)
            
            # Save detection to database periodically (every 30 seconds)
            current_time = time.time()
            if current_time - last_db_save >= db_save_interval:
                save_detection_to_db(
                    dict(detector.vehicle_counts),
                    detector.total_vehicles,
                    detector.conf_threshold,
                    inference_time
                )
                last_db_save = current_time
            
            # Save frame if requested and vehicles detected
            if save_frames and len(detections) > 0:
                timestamp = int(time.time() * 1000)
                cv2.imwrite(f"detection_{timestamp}.jpg", annotated_frame)
            
            # Write to output video
            if writer:
                writer.write(annotated_frame)
            
            # Display frame
            if display:
                try:
                    cv2.imshow('Vehicle Detection', annotated_frame)
                    
                    # Check for quit key
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        print("[INFO] Quit requested by user")
                        break
                    elif key == ord('s'):
                        # Save current frame on 's' key
                        timestamp = int(time.time() * 1000)
                        cv2.imwrite(f"screenshot_{timestamp}.jpg", annotated_frame)
                        print(f"[INFO] Screenshot saved: screenshot_{timestamp}.jpg")
                except cv2.error as e:
                    print(f"[WARNING] Display not available (headless mode): {e}")
                    print("[INFO] Detection running in headless mode. Press Ctrl+C to stop.")
                    # Sleep briefly to prevent high CPU usage in headless mode
                    time.sleep(0.01)
    
    except KeyboardInterrupt:
        print("[INFO] Interrupted by user")
    
    finally:
        # Save final detection to database
        save_detection_to_db(
            dict(detector.vehicle_counts),
            detector.total_vehicles,
            detector.conf_threshold,
            0
        )
        
        # Cleanup
        if use_picam:
            picam.stop()
            picam.close()
        else:
            cap.release()
        if writer:
            writer.release()
        try:
            cv2.destroyAllWindows()
        except cv2.error:
            pass  # Ignore if GUI not available
        print("[INFO] Detection stopped")


def main():
    parser = argparse.ArgumentParser(
        description='Vehicle-Only Detection System for Raspberry Pi 5'
    )
    parser.add_argument(
        '--source', '-s',
        default='0',
        help='Video source: picam for RPi camera, 0 for webcam, or path to video file (default: 0)'
    )
    parser.add_argument(
        '--model', '-m',
        default='yolov8n.pt',
        help='Path to YOLO model (default: yolov8n.pt)'
    )
    parser.add_argument(
        '--conf', '-c',
        type=float,
        default=0.4,
        help='Confidence threshold (default: 0.4)'
    )
    parser.add_argument(
        '--iou',
        type=float,
        default=0.5,
        help='IoU threshold for NMS (default: 0.5)'
    )
    parser.add_argument(
        '--output', '-o',
        help='Path to save output video (optional)'
    )
    parser.add_argument(
        '--no-display',
        action='store_true',
        help='Run without display (headless mode)'
    )
    parser.add_argument(
        '--save-frames',
        action='store_true',
        help='Save frames with detections'
    )
    parser.add_argument(
        '--input-size',
        type=int,
        default=640,
        choices=[320, 416, 480, 640, 960, 1280],
        help='Model input size - larger = better accuracy (default: 640)'
    )
    parser.add_argument(
        '--enhance',
        action='store_true',
        help='Enable image enhancement for better detection quality'
    )
    parser.add_argument(
        '--no-track',
        action='store_true',
        help='Disable vehicle tracking (tracking is enabled by default)'
    )
    parser.add_argument(
        '--counting-line',
        type=str,
        default=None,
        help='Set counting line as x1,y1-x2,y2 (e.g., "0,360-640,360")'
    )
    parser.add_argument(
        '--counting-direction',
        type=str,
        default='both',
        choices=['up', 'down', 'both'],
        help='Counting direction: up, down, or both (default: both)'
    )
    parser.add_argument(
        '--pixels-per-meter',
        type=float,
        default=10.0,
        help='Speed calibration: pixels per meter (default: 10.0)'
    )
    parser.add_argument(
        '--speed-threshold',
        type=float,
        default=60.0,
        help='Speed threshold for alerts in km/h (default: 60.0)'
    )
    parser.add_argument(
        '--count-threshold',
        type=int,
        default=5,
        help='Vehicle count threshold for alerts (default: 5)'
    )
    parser.add_argument(
        '--enable-heatmap',
        action='store_true',
        help='Enable traffic density heatmap visualization'
    )
    parser.add_argument(
        '--enable-color-detection',
        action='store_true',
        help='Enable vehicle color detection'
    )
    parser.add_argument(
        '--color-confidence',
        type=float,
        default=0.5,
        help='Color detection confidence threshold (default: 0.5)'
    )
    parser.add_argument(
        '--enable-violation-detection',
        action='store_true',
        help='Enable traffic violation detection'
    )
    parser.add_argument(
        '--speed-limit',
        type=float,
        default=60.0,
        help='Speed limit for violation detection in km/h (default: 60.0)'
    )
    parser.add_argument(
        '--export-onnx',
        action='store_true',
        help='Export model to ONNX format for faster inference'
    )
    parser.add_argument(
        '--width', '-w',
        type=int,
        default=None,
        help='Custom width for video capture (default: use camera native resolution)'
    )
    parser.add_argument(
        '--height',
        type=int,
        default=None,
        help='Custom height for video capture (default: use camera native resolution)'
    )
    
    args = parser.parse_args()
    
    # Export to ONNX if requested
    if args.export_onnx:
        print("[INFO] Exporting model to ONNX format...")
        model = YOLO(args.model)
        model.export(format='onnx', imgsz=args.input_size, dynamic=False)
        print("[INFO] ONNX export complete. Use the .onnx file with --model")
        return
    
    # Initialize detector
    detector = VehicleDetector(
        model_path=args.model,
        conf_threshold=args.conf,
        iou_threshold=args.iou,
        input_size=args.input_size,
        enable_enhancement=args.enhance,
        enable_tracking=not args.no_track
    )
    
    # Set counting line if specified
    if args.counting_line:
        try:
            parts = args.counting_line.split('-')
            p1 = tuple(int(x) for x in parts[0].split(','))
            p2 = tuple(int(x) for x in parts[1].split(','))
            detector.set_counting_line(p1, p2, direction=args.counting_direction)
        except (ValueError, IndexError):
            print("[ERROR] Invalid counting line format. Use x1,y1-x2,y2 (e.g., '0,360-640,360')")
            return
    
    # Set speed calibration
    detector.set_speed_calibration(args.pixels_per_meter)
    
    # Set alert thresholds
    detector.set_speed_threshold(args.speed_threshold)
    detector.set_vehicle_count_threshold(args.count_threshold)
    
    # Enable heatmap if requested
    if args.enable_heatmap:
        detector.enable_heatmap()
    
    # Enable color detection if requested
    if args.enable_color_detection:
        detector.enable_color_detection(confidence_threshold=args.color_confidence)
    
    # Enable violation detection if requested
    if args.enable_violation_detection:
        detector.enable_violation_detection(speed_limit=args.speed_limit)
    
    # Process video
    process_video(
        detector,
        args.source,
        output_path=args.output,
        display=not args.no_display,
        save_frames=args.save_frames,
        custom_width=args.width,
        custom_height=args.height
    )


if __name__ == '__main__':
    main()
