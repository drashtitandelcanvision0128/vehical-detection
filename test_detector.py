"""
Test script for Vehicle Detection System
Quick verification that the detector works correctly
"""

import cv2
import numpy as np
from vehicle_detector import VehicleDetector

def test_with_synthetic_image():
    """Test detector with synthetic images containing shapes"""
    print("="*50)
    print("TEST 1: Synthetic Image Test")
    print("="*50)
    
    # Create synthetic test images (since we don't have real video)
    print("[INFO] Creating synthetic test frame...")
    
    # Create a blank frame
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Add some colored rectangles (simulating different objects)
    # White rectangle (simulating background/object)
    cv2.rectangle(frame, (50, 50), (150, 150), (255, 255, 255), -1)
    
    # Blue rectangle (simulating car-like object)
    cv2.rectangle(frame, (200, 100), (350, 200), (255, 0, 0), -1)
    
    # Red rectangle (simulating vehicle)
    cv2.rectangle(frame, (400, 150), (550, 250), (0, 0, 255), -1)
    
    print("[INFO] Note: Synthetic test won't detect actual vehicles")
    print("[INFO] This test verifies the detector loads and runs")
    
    # Initialize detector
    try:
        detector = VehicleDetector(
            model_path='yolov8n.pt',
            conf_threshold=0.4,
            input_size=320  # Use smaller size for quick test
        )
        print("✓ Detector initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize detector: {e}")
        return False
    
    # Run detection
    try:
        annotated_frame, detections = detector.detect(frame)
        print(f"✓ Detection completed. Found {len(detections)} vehicles")
        
        for det in detections:
            print(f"  - {det['class_name']}: {det['conf']:.2f}")
        
        return True
    except Exception as e:
        print(f"✗ Detection failed: {e}")
        return False


def test_class_filtering():
    """Test that only vehicle classes are detected"""
    print("\n" + "="*50)
    print("TEST 2: Class Filtering Test")
    print("="*50)
    
    from vehicle_detector import VEHICLE_CLASSES
    
    expected_classes = {
        2: 'car',
        3: 'motorcycle',
        5: 'bus',
        7: 'truck'
    }
    
    print("[INFO] Checking vehicle class filtering...")
    
    if VEHICLE_CLASSES == expected_classes:
        print("✓ Vehicle classes correctly configured")
        print("  Detected classes:")
        for class_id, name in VEHICLE_CLASSES.items():
            print(f"    {class_id}: {name}")
        return True
    else:
        print("✗ Vehicle classes mismatch")
        return False


def test_model_download():
    """Test that YOLO model can be downloaded"""
    print("\n" + "="*50)
    print("TEST 3: Model Download Test")
    print("="*50)
    
    try:
        from ultralytics import YOLO
        import os
        
        model_path = 'yolov8n.pt'
        
        if os.path.exists(model_path):
            print(f"✓ Model already exists: {model_path}")
            return True
        
        print("[INFO] Downloading YOLOv8n model...")
        model = YOLO('yolov8n.pt')
        
        if os.path.exists(model_path):
            print(f"✓ Model downloaded successfully: {model_path}")
            return True
        else:
            print("✗ Model download failed")
            return False
            
    except Exception as e:
        print(f"✗ Model download failed: {e}")
        return False


def test_video_capture():
    """Test video capture device"""
    print("\n" + "="*50)
    print("TEST 4: Video Capture Test")
    print("="*50)
    
    print("[INFO] Testing video capture...")
    
    # Try webcam
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print("✓ Webcam accessible")
            print(f"  Resolution: {frame.shape[1]}x{frame.shape[0]}")
            cap.release()
            return True
        else:
            print("⚠ Webcam opened but cannot read frames")
    else:
        print("⚠ Webcam not available (this is OK for headless systems)")
    
    cap.release()
    return True  # Not a failure if no webcam


def print_summary(results):
    """Print test summary"""
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    total = len(results)
    passed = sum(results.values())
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print("-"*50)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! System ready.")
    else:
        print("\n⚠ Some tests failed. Check output above.")


def main():
    """Run all tests"""
    print("\n" + "="*50)
    print("VEHICLE DETECTION SYSTEM - TEST SUITE")
    print("="*50)
    
    results = {}
    
    # Run tests
    results['Class Filtering'] = test_class_filtering()
    results['Model Download'] = test_model_download()
    results['Synthetic Detection'] = test_with_synthetic_image()
    results['Video Capture'] = test_video_capture()
    
    # Print summary
    print_summary(results)
    
    return all(results.values())


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
