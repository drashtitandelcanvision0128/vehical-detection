# Vehicle-Only Detection System for Raspberry Pi 5

A real-time object detection system optimized for Raspberry Pi 5 that detects only vehicles (Car, Motorcycle, Bus, Truck) from live video streams.

## Features

- **Vehicle-Only Detection**: Detects only Cars, Motorcycles, Buses, and Trucks
- **High Performance**: Optimized for Raspberry Pi 5 with YOLOv8 Nano
- **Real-time Processing**: Achieves 15-25 FPS on Raspberry Pi 5
- **ONNX Support**: Optional ONNX export for faster inference
- **Vehicle Counting**: Built-in vehicle counting per class
- **Flexible Input**: Supports webcam and video files

## Quick Start

### 1. Installation

```bash
# Run the setup script
chmod +x setup.sh
./setup.sh

# Or manually install:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Download Model

```bash
# The model will auto-download on first run, or:
python3 -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
```

### 3. Run Detection

```bash
# Webcam
python3 vehicle_detector.py --source 0

# Video file
python3 vehicle_detector.py --source traffic.mp4

# Save output video
python3 vehicle_detector.py --source 0 --output result.mp4
```

## Usage Options

```bash
python3 vehicle_detector.py [OPTIONS]

Options:
  -s, --source      Video source (0 for webcam, or path)
  -m, --model       Model path (default: yolov8n.pt)
  -c, --conf        Confidence threshold (default: 0.4)
  --iou             IoU threshold for NMS (default: 0.5)
  -o, --output      Save output video path
  --no-display      Run without display (headless)
  --save-frames     Save frames with detections
  --input-size      Model input size: 320, 416, 480, 640
  --export-onnx     Export model to ONNX format
```

### Performance Tuning

```bash
# Fastest (lower resolution)
python3 vehicle_detector.py --source 0 --input-size 320 --conf 0.5

# Balanced (recommended)
python3 vehicle_detector.py --source 0 --input-size 480 --conf 0.4

# Higher accuracy
python3 vehicle_detector.py --source 0 --input-size 640 --conf 0.3
```

## Testing

### Test Case 1: Webcam with Mixed Objects

1. Run: `python3 vehicle_detector.py --source 0`
2. Show the webcam:
   - A person standing → Should NOT be detected
   - A toy car → Should be detected as "car"
   - A toy motorcycle → Should be detected as "motorcycle"

### Test Case 2: Road Traffic Video

```bash
python3 vehicle_detector.py --source traffic_video.mp4
```

Expected output:
- Cars: Bounding boxes with green labels
- Motorcycles: Bounding boxes with magenta labels
- Buses: Bounding boxes with yellow labels
- Trucks: Bounding boxes with red labels
- Pedestrians: No boxes (filtered out)

### Test Case 3: Save Detections

```bash
python3 vehicle_detector.py --source 0 --save-frames --output detected.mp4
```

## Performance Expectations

| Input Size | Raspberry Pi 5 FPS | Accuracy |
|------------|-------------------|----------|
| 320x320    | 20-25 FPS         | Good     |
| 416x416    | 15-20 FPS         | Better   |
| 480x480    | 12-18 FPS         | Better   |
| 640x640    | 8-12 FPS          | Best     |

## ONNX Optimization (Bonus)

Export to ONNX for faster inference:

```bash
# Export model
python3 vehicle_detector.py --export-onnx

# Use ONNX model
python3 vehicle_detector.py --model yolov8n.onnx --source 0
```

## Project Structure

```
vehicle-detection/
├── vehicle_detector.py    # Main detection script
├── requirements.txt       # Python dependencies
├── setup.sh              # Installation script
├── README.md             # This file
├── yolov8n.pt            # YOLOv8 nano model (auto-downloaded)
└── venv/                 # Virtual environment
```

## Troubleshooting

### Low FPS Issues
1. Reduce input size: `--input-size 320`
2. Increase confidence threshold: `--conf 0.5`
3. Close other applications
4. Use ONNX model for faster inference

### Camera Not Working
```bash
# Test camera
libcamera-hello --timeout 0

# For legacy camera support
export OPENCV_VIDEOIO_PRIORITY_MSMF=0
```

### Memory Issues
```bash
# Increase swap size
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Set CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

## Keyboard Controls

| Key | Action |
|-----|--------|
| `q` | Quit |
| `s` | Save screenshot |

## Vehicle Classes

The system detects only these COCO classes:

| Class ID | Name      | Color   |
|----------|-----------|---------|
| 2        | car       | Green   |
| 3        | motorcycle| Magenta |
| 5        | bus       | Yellow  |
| 7        | truck     | Red     |

All other objects (person, dog, cat, chair, etc.) are automatically filtered out.

## License

MIT License
