"""
Advanced Vehicle Detection System with:
- Direction-based vehicle counting
- Speed estimation
- Line crossing detection
- Save to JSON/CSV
"""

import cv2
import numpy as np
from ultralytics import YOLO
import argparse
import time
from collections import defaultdict, deque
import json
import csv
from datetime import datetime

# Vehicle classes
VEHICLE_CLASSES = {
    2: 'car',
    3: 'motorcycle',
    5: 'bus',
    7: 'truck'
}

CLASS_COLORS = {
    'car': (0, 255, 0),
    'motorcycle': (255, 0, 255),
    'bus': (0, 255, 255),
    'truck': (0, 0, 255)
}


class VehicleTracker:
    """Track vehicles across frames for counting and speed estimation"""
    
    def __init__(self, max_disappeared=30, max_distance=50):
        self.next_id = 0
        self.vehicles = {}
        self.disappeared = {}
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance
        self.count_up = 0
        self.count_down = 0
        self.counted_ids = set()
        
    def calculate_center(self, bbox):
        """Calculate center point of bounding box"""
        x1, y1, x2, y2 = bbox
        return ((x1 + x2) // 2, (y1 + y2) // 2)
    
    def calculate_distance(self, p1, p2):
        """Calculate Euclidean distance between two points"""
        return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
    
    def register(self, bbox, class_name):
        """Register a new vehicle"""
        self.vehicles[self.next_id] = {
            'bbox': bbox,
            'center': self.calculate_center(bbox),
            'class': class_name,
            'positions': deque(maxlen=10),
            'speed': 0,
            'first_seen': time.time()
        }
        self.vehicles[self.next_id]['positions'].append(self.calculate_center(bbox))
        self.disappeared[self.next_id] = 0
        self.next_id += 1
        return self.next_id - 1
    
    def deregister(self, vehicle_id):
        """Remove a vehicle from tracking"""
        del self.vehicles[vehicle_id]
        del self.disappeared[vehicle_id]
    
    def update(self, detections, count_line_y=None, frame_height=None):
        """Update tracker with new detections"""
        if len(detections) == 0:
            for vehicle_id in list(self.disappeared.keys()):
                self.disappeared[vehicle_id] += 1
                if self.disappeared[vehicle_id] > self.max_disappeared:
                    self.deregister(vehicle_id)
            return self.vehicles
        
        input_centers = []
        for det in detections:
            center = self.calculate_center(det['box'])
            input_centers.append((center, det))
        
        if len(self.vehicles) == 0:
            for center, det in input_centers:
                self.register(det['box'], det['class_name'])
        else:
            vehicle_ids = list(self.vehicles.keys())
            vehicle_centers = [self.vehicles[v_id]['center'] for v_id in vehicle_ids]
            
            used = set()
            for center, det in input_centers:
                distances = []
                for v_id, v_center in zip(vehicle_ids, vehicle_centers):
                    if v_id not in used:
                        dist = self.calculate_distance(center, v_center)
                        distances.append((dist, v_id))
                
                if distances:
                    distances.sort()
                    min_dist, closest_id = distances[0]
                    
                    if min_dist <= self.max_distance:
                        self.vehicles[closest_id]['bbox'] = det['box']
                        self.vehicles[closest_id]['center'] = center
                        self.vehicles[closest_id]['positions'].append(center)
                        self.disappeared[closest_id] = 0
                        used.add(closest_id)
                        
                        # Check line crossing for counting
                        if count_line_y and closest_id not in self.counted_ids:
                            prev_center = self.vehicles[closest_id]['positions'][0] if len(self.vehicles[closest_id]['positions']) > 1 else center
                            
                            # Check if crossed the line
                            if prev_center[1] < count_line_y and center[1] >= count_line_y:
                                self.count_down += 1
                                self.counted_ids.add(closest_id)
                            elif prev_center[1] > count_line_y and center[1] <= count_line_y:
                                self.count_up += 1
                                self.counted_ids.add(closest_id)
                    else:
                        self.register(det['box'], det['class_name'])
                else:
                    self.register(det['box'], det['class_name'])
            
            # Mark unused vehicles as disappeared
            for v_id in vehicle_ids:
                if v_id not in used:
                    self.disappeared[v_id] += 1
                    if self.disappeared[v_id] > self.max_disappeared:
                        self.deregister(v_id)
        
        return self.vehicles


class AdvancedVehicleDetector:
    """Advanced vehicle detector with tracking and counting"""
    
    def __init__(self, model_path='yolov8n.pt', conf_threshold=0.4, 
                 iou_threshold=0.5, input_size=640, enable_tracking=True):
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.input_size = input_size
        self.enable_tracking = enable_tracking
        
        # Load model
        print(f"[INFO] Loading model: {model_path}")
        self.model = YOLO(model_path)
        
        # Initialize tracker
        if enable_tracking:
            self.tracker = VehicleTracker()
        
        # Data logging
        self.detection_log = []
        
        # Warm up
        print("[INFO] Warming up model...")
        dummy_input = np.zeros((input_size, input_size, 3), dtype=np.uint8)
        self.model.predict(dummy_input, verbose=False)
        print("[INFO] Model ready!")
    
    def detect(self, frame, count_line_y=None):
        """Run detection and tracking on frame"""
        results = self.model.predict(
            frame,
            imgsz=self.input_size,
            conf=self.conf_threshold,
            iou=self.iou_threshold,
            verbose=False,
            classes=list(VEHICLE_CLASSES.keys())
        )
        
        # Filter detections
        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
            
            for box in boxes:
                class_id = int(box.cls.item())
                conf = float(box.conf.item())
                
                if class_id in VEHICLE_CLASSES and conf >= self.conf_threshold:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    class_name = VEHICLE_CLASSES[class_id]
                    detections.append({
                        'box': (int(x1), int(y1), int(x2), int(y2)),
                        'class_id': class_id,
                        'conf': conf,
                        'class_name': class_name
                    })
        
        # Update tracker
        if self.enable_tracking:
            self.tracker.update(detections, count_line_y, frame.shape[0])
        
        # Log detections
        timestamp = datetime.now().isoformat()
        for det in detections:
            self.detection_log.append({
                'timestamp': timestamp,
                'class': det['class_name'],
                'confidence': det['conf'],
                'bbox': det['box']
            })
        
        return detections
    
    def draw_detections(self, frame, detections, count_line_y=None):
        """Draw detections, tracking IDs, and counting line"""
        annotated = frame.copy()
        
        # Draw counting line
        if count_line_y:
            cv2.line(annotated, (0, count_line_y), (frame.shape[1], count_line_y), (0, 255, 255), 2)
            cv2.putText(annotated, "Counting Line", (10, count_line_y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
        
        # Draw tracked vehicles
        if self.enable_tracking and hasattr(self, 'tracker'):
            for v_id, vehicle in self.tracker.vehicles.items():
                x1, y1, x2, y2 = vehicle['bbox']
                class_name = vehicle['class']
                color = CLASS_COLORS.get(class_name, (0, 255, 0))
                
                # Draw bounding box
                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                
                # Draw ID and class
                label = f"ID:{v_id} {class_name}"
                cv2.putText(annotated, label, (x1, y1 - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                
                # Draw center point
                center = vehicle['center']
                cv2.circle(annotated, center, 4, (255, 255, 255), -1)
                
                # Draw trail
                positions = list(vehicle['positions'])
                for i in range(1, len(positions)):
                    cv2.line(annotated, positions[i-1], positions[i], color, 2)
        else:
            # Draw without tracking
            for det in detections:
                x1, y1, x2, y2 = det['box']
                class_name = det['class_name']
                conf = det['conf']
                color = CLASS_COLORS.get(class_name, (0, 255, 0))
                
                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                label = f"{class_name}: {conf:.2f}"
                cv2.putText(annotated, label, (x1, y1 - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        return annotated
    
    def draw_stats(self, frame, fps):
        """Draw statistics overlay"""
        # Background for stats
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (300, 150), (0, 0, 0), -1)
        frame = cv2.addWeighted(frame, 1, overlay, 0.3, 0)
        
        # FPS
        cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        if self.enable_tracking and hasattr(self, 'tracker'):
            # Counts
            cv2.putText(frame, f"Up: {self.tracker.count_up} | Down: {self.tracker.count_down}",
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(frame, f"Active Vehicles: {len(self.tracker.vehicles)}",
                       (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return frame
    
    def save_log(self, filename='detection_log.json'):
        """Save detection log to JSON"""
        with open(filename, 'w') as f:
            json.dump(self.detection_log, f, indent=2)
        print(f"[INFO] Saved detection log to {filename}")
    
    def save_csv(self, filename='detection_log.csv'):
        """Save detection log to CSV"""
        if not self.detection_log:
            return
        
        keys = self.detection_log[0].keys()
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(self.detection_log)
        print(f"[INFO] Saved detection log to {filename}")


def main():
    parser = argparse.ArgumentParser(description='Advanced Vehicle Detector')
    parser.add_argument('--source', '-s', default='0', help='Video source')
    parser.add_argument('--model', '-m', default='yolov8n.pt', help='Model path')
    parser.add_argument('--conf', '-c', type=float, default=0.4, help='Confidence threshold')
    parser.add_argument('--iou', type=float, default=0.5, help='IoU threshold')
    parser.add_argument('--input-size', type=int, default=640, help='Input size')
    parser.add_argument('--no-tracking', action='store_true', help='Disable tracking')
    parser.add_argument('--count-line', type=float, default=0.5, 
                       help='Counting line position (0-1, default: 0.5)')
    parser.add_argument('--output', '-o', help='Output video path')
    parser.add_argument('--save-json', help='Save detections to JSON file')
    parser.add_argument('--save-csv', help='Save detections to CSV file')
    
    args = parser.parse_args()
    
    # Initialize detector
    detector = AdvancedVehicleDetector(
        model_path=args.model,
        conf_threshold=args.conf,
        iou_threshold=args.iou,
        input_size=args.input_size,
        enable_tracking=not args.no_tracking
    )
    
    # Open video source
    source = int(args.source) if args.source.isdigit() else args.source
    cap = cv2.VideoCapture(source)
    
    if not cap.isOpened():
        print(f"[ERROR] Cannot open video source: {args.source}")
        return
    
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    count_line_y = int(frame_height * args.count_line)
    
    # Video writer
    writer = None
    if args.output:
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(args.output, fourcc, 20, (frame_width, frame_height))
    
    # FPS calculation
    fps = 0
    frame_count = 0
    start_time = time.time()
    
    print("[INFO] Starting detection... Press 'q' to quit, 's' to save log")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Detect and track
            detections = detector.detect(frame, count_line_y)
            annotated = detector.draw_detections(frame, detections, count_line_y)
            
            # Calculate FPS
            frame_count += 1
            elapsed = time.time() - start_time
            if elapsed > 1.0:
                fps = frame_count / elapsed
                frame_count = 0
                start_time = time.time()
            
            # Draw stats
            annotated = detector.draw_stats(annotated, fps)
            
            # Save video
            if writer:
                writer.write(annotated)
            
            # Display
            cv2.imshow('Advanced Vehicle Detector', annotated)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                if args.save_json:
                    detector.save_log(args.save_json)
                if args.save_csv:
                    detector.save_csv(args.save_csv)
    
    finally:
        # Save logs
        if args.save_json:
            detector.save_log(args.save_json)
        if args.save_csv:
            detector.save_csv(args.save_csv)
        
        cap.release()
        if writer:
            writer.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
