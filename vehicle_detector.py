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
                 use_onnx=False, input_size=640):
        """
        Initialize Vehicle Detector
        
        Args:
            model_path: Path to YOLO model
            conf_threshold: Confidence threshold for detections
            iou_threshold: IoU threshold for NMS
            use_onnx: Use ONNX runtime for faster inference
            input_size: Input size for model (smaller = faster)
        """
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.input_size = input_size
        self.vehicle_counts = defaultdict(int)
        self.total_vehicles = 0
        
        # Load model
        print(f"[INFO] Loading model: {model_path}")
        self.model = YOLO(model_path)
        
        # Warm up model
        print("[INFO] Warming up model...")
        dummy_input = np.zeros((input_size, input_size, 3), dtype=np.uint8)
        self.model.predict(dummy_input, verbose=False)
        print("[INFO] Model ready!")
    
    def filter_vehicle_detections(self, results):
        """
        Filter detections to keep only vehicle classes
        
        Args:
            results: YOLO detection results
            
        Returns:
            List of filtered detections [(box, class_id, conf, class_name)]
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
                    filtered_detections.append({
                        'box': (int(x1), int(y1), int(x2), int(y2)),
                        'class_id': class_id,
                        'conf': conf,
                        'class_name': class_name
                    })
        
        return filtered_detections
    
    def draw_detections(self, frame, detections):
        """
        Draw bounding boxes and labels for vehicle detections
        
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
            color = CLASS_COLORS.get(class_name, (0, 255, 0))
            
            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Prepare label
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
        
        return frame
    
    def update_counts(self, detections):
        """Update vehicle counts"""
        current_frame_counts = defaultdict(int)
        for det in detections:
            current_frame_counts[det['class_name']] += 1
        
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
        
        y_offset += 25
        for class_name, count in self.vehicle_counts.items():
            color = CLASS_COLORS.get(class_name, (255, 255, 255))
            cv2.putText(
                frame, f"  {class_name}: {count}", (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1
            )
            y_offset += 20
        
        return frame
    
    def detect(self, frame):
        """
        Run detection on a single frame
        
        Args:
            frame: Input frame (BGR image)
            
        Returns:
            Annotated frame and list of detections
        """
        # Run inference with smaller input size for speed
        results = self.model.predict(
            frame,
            imgsz=self.input_size,
            conf=self.conf_threshold,
            iou=self.iou_threshold,
            verbose=False,
            classes=list(VEHICLE_CLASSES.keys())  # Filter at model level
        )
        
        # Filter detections
        detections = self.filter_vehicle_detections(results)
        
        # Update counts
        self.update_counts(detections)
        
        # Draw detections
        annotated_frame = self.draw_detections(frame.copy(), detections)
        
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
        cv2.destroyAllWindows()
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
        choices=[320, 416, 480, 640],
        help='Model input size - smaller = faster (default: 640)'
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
        input_size=args.input_size
    )
    
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
