"""
Vehicle Detection Testing App using Gradio
Upload images or videos to test vehicle detection
"""

import gradio as gr
import cv2
import numpy as np
from ultralytics import YOLO
import tempfile
import os
import time
from pathlib import Path

# Vehicle-only classes from COCO dataset
VEHICLE_CLASSES = {
    2: 'car',
    3: 'motorcycle',
    5: 'bus',
    7: 'truck'
}

# Colors for each vehicle class (RGB for Gradio/PIL)
CLASS_COLORS = {
    'car': (0, 255, 0),        # Green
    'motorcycle': (255, 0, 255),  # Magenta
    'bus': (255, 255, 0),      # Yellow (BGR to RGB conversion)
    'truck': (255, 0, 0)       # Red
}

# Load model once at startup
print("[INFO] Loading YOLOv8n model...")
model = YOLO('yolov8n.pt')
print("[INFO] Model loaded successfully!")


def detect_vehicles_image(image_path, conf_threshold=0.4):
    """
    Process image and detect only vehicles
    
    Args:
        image_path: Path to uploaded image
        conf_threshold: Confidence threshold
        
    Returns:
        tuple: (annotated_image, status_message, processing_time, detections_count)
    """
    start_time = time.time()
    
    # Read image
    image = cv2.imread(image_path)
    if image is None:
        return None, "❌ Error: Could not read image file", 0, 0
    
    # Convert BGR to RGB for display
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Run detection
    results = model.predict(
        image,
        imgsz=640,
        conf=conf_threshold,
        verbose=False,
        classes=list(VEHICLE_CLASSES.keys())
    )
    
    # Filter and draw detections
    detections = []
    annotated = image.copy()
    
    for result in results:
        boxes = result.boxes
        if boxes is None:
            continue
        
        for box in boxes:
            class_id = int(box.cls.item())
            conf = float(box.conf.item())
            
            if class_id in VEHICLE_CLASSES:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                class_name = VEHICLE_CLASSES[class_id]
                detections.append({
                    'class': class_name,
                    'confidence': conf,
                    'bbox': (int(x1), int(y1), int(x2), int(y2))
                })
                
                # Draw bounding box (BGR)
                color = CLASS_COLORS[class_name]
                cv2.rectangle(annotated, (int(x1), int(y1)), (int(x2), int(y2)), color, 3)
                
                # Draw label
                label = f"{class_name}: {conf:.2f}"
                (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                cv2.rectangle(annotated, (int(x1), int(y1) - label_h - 10), 
                            (int(x1) + label_w, int(y1)), color, -1)
                cv2.putText(annotated, label, (int(x1), int(y1) - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
    
    # Convert to RGB for Gradio
    annotated_rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
    
    # Calculate processing time
    processing_time = time.time() - start_time
    
    # Prepare status message
    if len(detections) > 0:
        class_counts = {}
        for det in detections:
            class_name = det['class']
            class_counts[class_name] = class_counts.get(class_name, 0) + 1
        
        status = f"✅ Detected {len(detections)} vehicle(s):\n"
        for cls, count in class_counts.items():
            status += f"   • {cls}: {count}\n"
    else:
        status = "❌ No vehicles detected"
    
    return annotated_rgb, status, f"{processing_time:.3f}s", len(detections)


def detect_vehicles_video(video_path, conf_threshold=0.4, progress=gr.Progress()):
    """
    Process video and detect only vehicles
    
    Args:
        video_path: Path to uploaded video
        conf_threshold: Confidence threshold
        progress: Gradio progress callback
        
    Returns:
        tuple: (output_video_path, status_message, fps_info, total_detections)
    """
    start_time = time.time()
    
    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None, "❌ Error: Could not open video file", "", 0
    
    # Get video properties
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Create output video
    output_path = tempfile.mktemp(suffix='.mp4')
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))
    
    frame_count = 0
    total_detections = 0
    frame_detections = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Update progress
            if total_frames > 0:
                progress(frame_count / total_frames, desc=f"Processing frame {frame_count}/{total_frames}")
            
            # Detect vehicles
            results = model.predict(
                frame,
                imgsz=480,  # Smaller for video speed
                conf=conf_threshold,
                verbose=False,
                classes=list(VEHICLE_CLASSES.keys())
            )
            
            # Draw detections
            annotated = frame.copy()
            frame_has_detection = False
            
            for result in results:
                boxes = result.boxes
                if boxes is None:
                    continue
                
                for box in boxes:
                    class_id = int(box.cls.item())
                    conf = float(box.conf.item())
                    
                    if class_id in VEHICLE_CLASSES:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        class_name = VEHICLE_CLASSES[class_id]
                        
                        frame_has_detection = True
                        total_detections += 1
                        frame_detections += 1
                        
                        # Draw bounding box
                        color = CLASS_COLORS[class_name]
                        cv2.rectangle(annotated, (int(x1), int(y1)), 
                                    (int(x2), int(y2)), color, 2)
                        
                        # Draw label
                        label = f"{class_name}: {conf:.2f}"
                        (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
                        cv2.rectangle(annotated, (int(x1), int(y1) - label_h - 10),
                                    (int(x1) + label_w, int(y1)), color, -1)
                        cv2.putText(annotated, label, (int(x1), int(y1) - 5),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
            
            # Add frame info
            cv2.putText(annotated, f"Frame: {frame_count}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            writer.write(annotated)
            frame_count += 1
    
    finally:
        cap.release()
        writer.release()
    
    processing_time = time.time() - start_time
    avg_fps = frame_count / processing_time if processing_time > 0 else 0
    
    # Status message
    if frame_detections > 0:
        status = f"✅ Video processed successfully!\nDetected vehicles in {frame_detections} frames"
    else:
        status = "❌ No vehicles detected in video"
    
    fps_info = f"Processing: {avg_fps:.1f} FPS | Original: {fps:.1f} FPS | Frames: {frame_count}"
    
    return output_path, status, fps_info, total_detections


def create_interface():
    """Create Gradio interface"""
    
    # Custom CSS for styling
    custom_css = """
    .detection-box { 
        border: 2px solid #4CAF50; 
        border-radius: 10px; 
        padding: 10px;
        margin: 10px 0;
    }
    .success { color: #4CAF50; font-weight: bold; }
    .error { color: #f44336; font-weight: bold; }
    """
    
    with gr.Blocks(css=custom_css, title="Vehicle Detection Tester") as demo:
        gr.Markdown("""
        # 🚗 Vehicle Detection Testing App
        
        Upload an **image** or **video** to test vehicle detection.
        
        **Detects only:** Car, Motorcycle, Bus, Truck  
        **Ignores:** People, animals, buildings, etc.
        """)
        
        with gr.Tab("📷 Image Detection"):
            with gr.Row():
                with gr.Column():
                    image_input = gr.Image(
                        type="filepath",
                        label="Upload Image",
                        sources=["upload"]
                    )
                    conf_slider_img = gr.Slider(
                        minimum=0.1,
                        maximum=1.0,
                        value=0.4,
                        step=0.05,
                        label="Confidence Threshold"
                    )
                    detect_btn_img = gr.Button("🔍 Detect Vehicles", variant="primary")
                
                with gr.Column():
                    image_output = gr.Image(
                        label="Detected Vehicles",
                        type="numpy"
                    )
                    status_img = gr.Textbox(
                        label="Detection Status",
                        lines=5
                    )
                    with gr.Row():
                        time_img = gr.Textbox(label="Processing Time")
                        count_img = gr.Textbox(label="Detections Count")
        
        with gr.Tab("🎬 Video Detection"):
            with gr.Row():
                with gr.Column():
                    video_input = gr.Video(
                        label="Upload Video"
                    )
                    conf_slider_vid = gr.Slider(
                        minimum=0.1,
                        maximum=1.0,
                        value=0.4,
                        step=0.05,
                        label="Confidence Threshold"
                    )
                    detect_btn_vid = gr.Button("🔍 Detect Vehicles", variant="primary")
                
                with gr.Column():
                    video_output = gr.Video(
                        label="Processed Video"
                    )
                    status_vid = gr.Textbox(
                        label="Detection Status",
                        lines=3
                    )
                    with gr.Row():
                        fps_info = gr.Textbox(label="FPS Info")
                        count_vid = gr.Textbox(label="Total Detections")
        
        with gr.Tab("ℹ️ Info"):
            gr.Markdown("""
            ## Vehicle Classes Detected
            
            | Class | Color | COCO ID |
            |-------|-------|---------|
            | Car | 🟢 Green | 2 |
            | Motorcycle | 🟣 Magenta | 3 |
            | Bus | 🟡 Yellow | 5 |
            | Truck | 🔴 Red | 7 |
            
            ## Testing Tips
            
            1. **Upload traffic images** - Should detect cars, bikes, buses
            2. **Upload images with only people** - Should show "No vehicles detected"
            3. **Try different confidence thresholds** - Lower = more detections, Higher = fewer but more confident
            
            ## Examples to Try
            
            - Street view with cars and pedestrians → Only cars/bikes detected
            - Highway traffic → Multiple vehicles detected
            - Parking lot → Cars and motorcycles detected
            - Image with only a person → No detection
            """)
        
        # Event handlers
        detect_btn_img.click(
            fn=detect_vehicles_image,
            inputs=[image_input, conf_slider_img],
            outputs=[image_output, status_img, time_img, count_img]
        )
        
        detect_btn_vid.click(
            fn=detect_vehicles_video,
            inputs=[video_input, conf_slider_vid],
            outputs=[video_output, status_vid, fps_info, count_vid]
        )
        
        gr.Markdown("---")
        gr.Markdown("Built with ❤️ using YOLOv8 + Gradio")
    
    return demo


def main():
    """Launch the Gradio app"""
    demo = create_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True,  # Create public URL
        show_error=True
    )


if __name__ == "__main__":
    main()
