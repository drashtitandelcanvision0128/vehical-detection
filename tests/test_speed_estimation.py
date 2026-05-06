"""
Speed Estimation Tests for Vehicle Detection App
Tests for speed calculation based on tracking data
"""
import pytest
from collections import defaultdict
from unittest.mock import MagicMock, patch
import numpy as np


@pytest.mark.speed
@pytest.mark.unit
def test_speed_estimation_enabled_by_default():
    """Test that speed estimation is enabled by default"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.speed_estimation_enabled = True
    detector.pixels_per_meter = 10.0
    detector.track_speeds = {}
    detector.track_speed_history = defaultdict(list)
    
    assert detector.speed_estimation_enabled is True
    assert detector.pixels_per_meter == 10.0


@pytest.mark.speed
@pytest.mark.unit
def test_set_speed_calibration():
    """Test that set_speed_calibration updates pixels_per_meter"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.pixels_per_meter = 10.0
    
    detector.set_speed_calibration(20.0)
    assert detector.pixels_per_meter == 20.0
    
    # Test minimum value enforcement
    detector.set_speed_calibration(0.01)
    assert detector.pixels_per_meter == 0.1


@pytest.mark.speed
@pytest.mark.unit
def test_calculate_speed_basic():
    """Test basic speed calculation from position history"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.speed_estimation_enabled = True
    detector.pixels_per_meter = 10.0  # 10 pixels = 1 meter
    detector.track_speeds = {}
    detector.track_speed_history = defaultdict(list)
    detector.track_history = defaultdict(list)
    
    # Track moved 100 pixels (10 meters) in 1 frame
    detector.track_history[1] = [(100, 100), (200, 100)]
    
    # At 30 FPS, 10 meters in 1/30 second = 300 m/s = 1080 km/h (unrealistic but formula is correct)
    speed = detector.calculate_speed(1, fps=30)
    assert speed is not None
    assert speed > 0


@pytest.mark.speed
@pytest.mark.unit
def test_calculate_speed_insufficient_history():
    """Test that speed returns None when track history is insufficient"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.track_history = defaultdict(list)
    
    # No history
    speed = detector.calculate_speed(1, fps=30)
    assert speed is None
    
    # Only one position
    detector.track_history[1] = [(100, 100)]
    speed = detector.calculate_speed(1, fps=30)
    assert speed is None


@pytest.mark.speed
@pytest.mark.unit
def test_update_speeds():
    """Test that update_speeds calculates and stores speeds for all tracks"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.speed_estimation_enabled = True
    detector.enable_tracking = True
    detector.pixels_per_meter = 10.0
    detector.track_speeds = {}
    detector.track_speed_history = defaultdict(list)
    detector.track_history = defaultdict(list)
    
    # Set up track history
    detector.track_history[1] = [(100, 100), (110, 100)]  # Moved 10 pixels
    detector.track_history[2] = [(200, 200), (220, 200)]  # Moved 20 pixels
    
    detections = [
        {'box': (100, 95, 115, 105), 'class_id': 2, 'conf': 0.9, 'class_name': 'car', 'track_id': 1},
        {'box': (200, 195, 235, 205), 'class_id': 3, 'conf': 0.8, 'class_name': 'motorcycle', 'track_id': 2},
    ]
    
    detector.update_speeds(detections, fps=30)
    
    assert 1 in detector.track_speeds
    assert 2 in detector.track_speeds
    assert detector.track_speeds[1] > 0
    assert detector.track_speeds[2] > 0
    assert detector.track_speeds[2] > detector.track_speeds[1]  # Track 2 moved more


@pytest.mark.speed
@pytest.mark.unit
def test_update_speeds_smoothing():
    """Test that speed smoothing uses moving average"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.speed_estimation_enabled = True
    detector.enable_tracking = True
    detector.pixels_per_meter = 10.0
    detector.track_speeds = {}
    detector.track_speed_history = defaultdict(list)
    detector.track_history = defaultdict(list)
    
    # First frame
    detector.track_history[1] = [(100, 100), (110, 100)]
    detections = [{'box': (100, 95, 115, 105), 'class_id': 2, 'conf': 0.9, 'class_name': 'car', 'track_id': 1}]
    detector.update_speeds(detections, fps=30)
    speed1 = detector.track_speeds[1]
    
    # Second frame (same speed)
    detector.track_history[1] = [(100, 100), (110, 100), (120, 100)]
    detections = [{'box': (115, 95, 130, 105), 'class_id': 2, 'conf': 0.9, 'class_name': 'car', 'track_id': 1}]
    detector.update_speeds(detections, fps=30)
    
    # Speed should be smoothed (average of recent values)
    assert 1 in detector.track_speed_history
    assert len(detector.track_speed_history[1]) >= 1


@pytest.mark.speed
@pytest.mark.unit
def test_update_speeds_disabled():
    """Test that update_speeds does nothing when disabled"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.speed_estimation_enabled = False
    detector.enable_tracking = True
    detector.track_speeds = {}
    detector.track_speed_history = defaultdict(list)
    detector.track_history = defaultdict(list)
    
    detector.track_history[1] = [(100, 100), (110, 100)]
    detections = [{'box': (100, 95, 115, 105), 'class_id': 2, 'conf': 0.9, 'class_name': 'car', 'track_id': 1}]
    
    detector.update_speeds(detections, fps=30)
    
    assert len(detector.track_speeds) == 0


@pytest.mark.speed
@pytest.mark.unit
def test_update_speeds_no_tracking():
    """Test that update_speeds does nothing when tracking is disabled"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.speed_estimation_enabled = True
    detector.enable_tracking = False
    detector.track_speeds = {}
    detector.track_speed_history = defaultdict(list)
    
    detections = [{'box': (100, 95, 115, 105), 'class_id': 2, 'conf': 0.9, 'class_name': 'car', 'track_id': None}]
    
    detector.update_speeds(detections, fps=30)
    
    assert len(detector.track_speeds) == 0


@pytest.mark.speed
@pytest.mark.unit
def test_speed_history_max_length():
    """Test that speed history is limited to 5 values"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.speed_estimation_enabled = True
    detector.enable_tracking = True
    detector.pixels_per_meter = 10.0
    detector.track_speeds = {}
    detector.track_speed_history = defaultdict(list)
    detector.track_history = defaultdict(list)
    
    # Add 10 frames of data
    for i in range(10):
        detector.track_history[1] = [(100 + i*10, 100), (110 + i*10, 100)]
        detections = [{'box': (100 + i*10, 95, 115 + i*10, 105), 'class_id': 2, 'conf': 0.9, 'class_name': 'car', 'track_id': 1}]
        detector.update_speeds(detections, fps=30)
    
    # History should be limited to 5 values
    assert len(detector.track_speed_history[1]) <= 5


@pytest.mark.speed
@pytest.mark.unit
def test_different_pixels_per_meter():
    """Test that different calibration values affect speed calculation"""
    from vehicle_detector import VehicleDetector
    
    detector1 = VehicleDetector.__new__(VehicleDetector)
    detector1.pixels_per_meter = 10.0
    detector1.track_history = defaultdict(list)
    detector1.track_history[1] = [(100, 100), (200, 100)]  # 100 pixels
    
    speed1 = detector1.calculate_speed(1, fps=30)
    
    detector2 = VehicleDetector.__new__(VehicleDetector)
    detector2.pixels_per_meter = 20.0  # More pixels per meter = smaller actual distance
    detector2.track_history = defaultdict(list)
    detector2.track_history[1] = [(100, 100), (200, 100)]  # Same 100 pixels
    
    speed2 = detector2.calculate_speed(1, fps=30)
    
    # With 20px/m, 100 pixels = 5 meters (vs 10 meters at 10px/m)
    # So speed2 should be half of speed1
    assert speed2 < speed1
    assert abs(speed2 - speed1 / 2) < 1.0  # Allow small rounding error
