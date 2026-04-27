"""
Headless Vehicle Detector - No GUI required
Runs detection without cv2.imshow() - saves output to file
"""

import cv2
import numpy as np
from ultralytics import YOLO
import argparse
import time
from collections import defaultdict

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


def detect_vehicles(model, frame, conf_threshold=0.4, iou_threshold=0.5, input_size=640):
    """Run detection and return annotated frame with stats"""
    
    start_time = time.time()
    
    # Run inference
    results = model.predict(
        frame,
        imgsz=input_size,
        conf=conf_threshold,
        iou=iou_threshold,
        verbose=False,
        classes=list(VEHICLE_CLASSES.keys())
    )
    
    # Filter and count detections
    detections = []
    class_counts = defaultdict(int)
    
    annotated = frame.copy()
    
    for result in results:
        boxes = result.boxes
        if boxes is None:
            continue
            
        for box in boxes:
            class_id = int(box.cls.item())
            conf = float(box.conf.item())
            
            if class_id in VEHICLE_CLASSES and conf >= conf_threshold:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                class_name = VEHICLE_CLASSES[class_id]
                
                detections.append({
                    'box': (int(x1), int(y1), int(x2), int(y2)),
                    'class': class_name,
                    'conf': conf
                })
                class_counts[class_name] += 1
                
                # Draw bounding box
                color = CLASS_COLORS[class_name]
                cv2.rectangle(annotated, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                
                # Draw label
                label = f"{class_name}: {conf:.2f}"
                (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
                cv2.rectangle(annotated, (int(x1), int(y1) - label_h - 10), 
                           (int(x1) + label_w, int(y1)), color, -1)
                cv2.putText(annotated, label, (int(x1), int(y1) - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
    
    # Add stats overlay
    inference_time = time.time() - start_time
    fps = 1.0 / inference_time if inference_time > 0 else 0
    
    # Draw stats box
    cv2.rectangle(annotated, (0, 0), (300, 100), (0, 0, 0), -1)
    cv2.putText(annotated, f"FPS: {fps:.1f}", (10, 30),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(annotated, f"Total Vehicles: {len(detections)}", (10, 60),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    y_offset = 85
    for class_name, count in class_counts.items():
        color = CLASS_COLORS[class_name]
        cv2.putText(annotated, f"{class_name}: {count}", (10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        y_offset += 20
    
    return annotated, detections, class_counts, fps


def process_video_headless(source, output_path, model_path='yolov8n.pt', 
                           conf_threshold=0.4, iou_threshold=0.5, 
                           input_size=640, save_frames=False):
    """Process video without displaying (headless mode)"""
    
    print(f"[INFO] Loading model: {model_path}")
    model = YOLO(model_path)
    
    # Warm up
    print("[INFO] Warming up model...")
    dummy_input = np.zeros((input_size, input_size, 3), dtype=np.uint8)
    model.predict(dummy_input, verbose=False)
    print("[INFO] Model ready!")
    
    # Open video source
    if source.isdigit():
        source = int(source)
        cap = cv2.VideoCapture(source)
        # Use camera native resolution (no hardcoded limits)
        print("[INFO] Using camera native resolution")
    else:
        cap = cv2.VideoCapture(source)
    
    if not cap.isOpened():
        print(f"[ERROR] Cannot open video source: {source}")
        return
    
    # Get properties
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps_input = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"[INFO] Resolution: {frame_width}x{frame_height}, FPS: {fps_input:.1f}")
    if total_frames > 0:
        print(f"[INFO] Total frames: {total_frames}")
    
    # Create video writer
    writer = None
    if output_path:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(output_path, fourcc, 20, (frame_width, frame_height))
        print(f"[INFO] Saving to: {output_path}")
    
    # Process frames
    frame_count = 0
    total_vehicles = 0
    start_time = time.time()
    
    print("[INFO] Starting detection... (Press Ctrl+C to stop)")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[INFO] End of video")
                break
            
            # Detect vehicles
            annotated, detections, class_counts, fps = detect_vehicles(
                model, frame, conf_threshold, iou_threshold, input_size
            )
            
            total_vehicles += len(detections)
            frame_count += 1
            
            # Save frame if requested
            if save_frames and len(detections) > 0:
                timestamp = int(time.time() * 1000)
                cv2.imwrite(f"frame_{timestamp}.jpg", annotated)
            
            # Write to output
            if writer:
                writer.write(annotated)
            
            # Print progress every 30 frames
            if frame_count % 30 == 0:
                elapsed = time.time() - start_time
                avg_fps = frame_count / elapsed
                print(f"[PROGRESS] Frames: {frame_count}, Vehicles: {total_vehicles}, FPS: {avg_fps:.1f}")
    
    except KeyboardInterrupt:
        print("\n[INFO] Stopped by user")
    
    finally:
        cap.release()
        if writer:
            writer.release()
        
        # Print summary
        total_time = time.time() - start_time
        print(f"\n{'='*50}")
        print("SUMMARY")
        print(f"{'='*50}")
        print(f"Total frames processed: {frame_count}")
        print(f"Total vehicles detected: {total_vehicles}")
        print(f"Processing time: {total_time:.1f}s")
        print(f"Average FPS: {frame_count/total_time:.1f}" if total_time > 0 else "N/A")
        print(f"{'='*50}")


def main():
    parser = argparse.ArgumentParser(description='Vehicle Detector (Headless - No GUI)')
    parser.add_argument('--source', '-s', default='0', 
                       help='Video source: 0 for webcam, or path to video file')
    parser.add_argument('--output', '-o', required=True,
                       help='Output video path (required for headless mode)')
    parser.add_argument('--model', '-m', default='yolov8n.pt', help='Model path')
    parser.add_argument('--conf', '-c', type=float, default=0.4, help='Confidence threshold')
    parser.add_argument('--iou', type=float, default=0.5, help='IoU threshold')
    parser.add_argument('--input-size', type=int, default=640, choices=[320, 416, 480, 640],
                       help='Input size (smaller = faster)')
    parser.add_argument('--save-frames', action='store_true',
                       help='Save individual frames with detections')
    
    args = parser.parse_args()
    
    process_video_headless(
        source=args.source,
        output_path=args.output,
        model_path=args.model,
        conf_threshold=args.conf,
        iou_threshold=args.iou,
        input_size=args.input_size,
        save_frames=args.save_frames
    )


if __name__ == '__main__':
    main()
