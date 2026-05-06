"""
Vehicle Color Detection Tests for Vehicle Detection App
Tests for HSV-based vehicle color detection
"""
import pytest
import numpy as np
import cv2


@pytest.mark.color_detection
@pytest.mark.unit
def test_enable_color_detection():
    """Test that enable_color_detection properly initializes color detection"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.color_detection_enabled = False
    detector.color_confidence_threshold = 0.5
    
    detector.enable_color_detection(confidence_threshold=0.7)
    
    assert detector.color_detection_enabled is True
    assert detector.color_confidence_threshold == 0.7


@pytest.mark.color_detection
@pytest.mark.unit
def test_disable_color_detection():
    """Test that disable_color_detection disables color detection"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.color_detection_enabled = True
    
    detector.disable_color_detection()
    
    assert detector.color_detection_enabled is False


@pytest.mark.color_detection
@pytest.mark.unit
def test_detect_color_white():
    """Test detection of white color"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    
    # Create a white vehicle region
    white_frame = np.ones((100, 100, 3), dtype=np.uint8) * 255
    bbox = (0, 0, 100, 100)
    
    color, confidence = detector.detect_color(white_frame, bbox)
    
    # Should detect white with high confidence
    assert color == 'white'
    assert confidence > 0.5


@pytest.mark.color_detection
@pytest.mark.unit
def test_detect_color_black():
    """Test detection of black color"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    
    # Create a black vehicle region
    black_frame = np.zeros((100, 100, 3), dtype=np.uint8)
    bbox = (0, 0, 100, 100)
    
    color, confidence = detector.detect_color(black_frame, bbox)
    
    # Should detect black with high confidence
    assert color == 'black'
    assert confidence > 0.5


@pytest.mark.color_detection
@pytest.mark.unit
def test_detect_color_red():
    """Test detection of red color"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    
    # Create a red vehicle region
    red_frame = np.zeros((100, 100, 3), dtype=np.uint8)
    red_frame[:, :] = [0, 0, 255]  # BGR red
    bbox = (0, 0, 100, 100)
    
    color, confidence = detector.detect_color(red_frame, bbox)
    
    # Should detect red
    assert color == 'red'


@pytest.mark.color_detection
@pytest.mark.unit
def test_detect_color_blue():
    """Test detection of blue color"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    
    # Create a blue vehicle region
    blue_frame = np.zeros((100, 100, 3), dtype=np.uint8)
    blue_frame[:, :] = [255, 0, 0]  # BGR blue
    bbox = (0, 0, 100, 100)
    
    color, confidence = detector.detect_color(blue_frame, bbox)
    
    # Should detect blue
    assert color == 'blue'


@pytest.mark.color_detection
@pytest.mark.unit
def test_detect_color_green():
    """Test detection of green color"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    
    # Create a green vehicle region
    green_frame = np.zeros((100, 100, 3), dtype=np.uint8)
    green_frame[:, :] = [0, 255, 0]  # BGR green
    bbox = (0, 0, 100, 100)
    
    color, confidence = detector.detect_color(green_frame, bbox)
    
    # Should detect green
    assert color == 'green'


@pytest.mark.color_detection
@pytest.mark.unit
def test_detect_color_yellow():
    """Test detection of yellow color"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    
    # Create a yellow vehicle region
    yellow_frame = np.zeros((100, 100, 3), dtype=np.uint8)
    yellow_frame[:, :] = [0, 255, 255]  # BGR yellow
    bbox = (0, 0, 100, 100)
    
    color, confidence = detector.detect_color(yellow_frame, bbox)
    
    # Should detect yellow
    assert color == 'yellow'


@pytest.mark.color_detection
@pytest.mark.unit
def test_detect_color_empty_bbox():
    """Test color detection with empty bounding box"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    bbox = (50, 50, 50, 50)  # Empty box
    
    color, confidence = detector.detect_color(frame, bbox)
    
    # Should return unknown for empty region
    assert color == 'unknown'
    assert confidence == 0.0


@pytest.mark.color_detection
@pytest.mark.unit
def test_confidence_threshold_clamping():
    """Test that confidence threshold is clamped between 0 and 1"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.color_detection_enabled = False
    
    # Test with threshold > 1
    detector.enable_color_detection(confidence_threshold=1.5)
    assert detector.color_confidence_threshold == 1.0
    
    # Test with threshold < 0
    detector.enable_color_detection(confidence_threshold=-0.5)
    assert detector.color_confidence_threshold == 0.0


@pytest.mark.color_detection
@pytest.mark.unit
def test_color_detection_disabled():
    """Test that color detection is disabled by default"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.color_detection_enabled = False
    detector.color_confidence_threshold = 0.5
    
    assert detector.color_detection_enabled is False
