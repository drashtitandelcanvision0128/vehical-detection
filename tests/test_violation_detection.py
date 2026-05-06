"""
Traffic Violation Detection Tests for Vehicle Detection App
Tests for traffic violation detection system
"""
import pytest


@pytest.mark.violation_detection
@pytest.mark.unit
def test_enable_violation_detection():
    """Test that enable_violation_detection properly initializes violation detection"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.violation_detection_enabled = False
    detector.speed_limit = 60.0
    
    detector.enable_violation_detection(speed_limit=70.0)
    
    assert detector.violation_detection_enabled is True
    assert detector.speed_limit == 70.0


@pytest.mark.violation_detection
@pytest.mark.unit
def test_disable_violation_detection():
    """Test that disable_violation_detection disables violation detection"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.violation_detection_enabled = True
    
    detector.disable_violation_detection()
    
    assert detector.violation_detection_enabled is False


@pytest.mark.violation_detection
@pytest.mark.unit
def test_detect_violations_disabled():
    """Test that detect_violations returns empty when disabled"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.violation_detection_enabled = False
    
    detections = [{'box': (100, 100, 200, 200), 'class_name': 'car'}]
    
    violations = detector.detect_violations(detections)
    
    assert violations == []


@pytest.mark.violation_detection
@pytest.mark.unit
def test_detect_speeding_violation():
    """Test detection of speeding violations"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.violation_detection_enabled = True
    detector.speed_limit = 60.0
    detector.speed_estimation_enabled = True
    detector.enable_tracking = True
    detector.track_speeds = {1: 80.0}  # Vehicle going 80 km/h
    detector.violation_callbacks = []
    detector.detected_violations = []
    
    detections = [
        {'box': (100, 100, 200, 200), 'class_name': 'car', 'track_id': 1}
    ]
    
    violations = detector.detect_violations(detections)
    
    assert len(violations) == 1
    assert violations[0]['type'] == 'speeding'
    assert violations[0]['speed'] == 80.0
    assert violations[0]['excess'] == 20.0


@pytest.mark.violation_detection
@pytest.mark.unit
def test_no_violation_within_limit():
    """Test that no violation is detected when within speed limit"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.violation_detection_enabled = True
    detector.speed_limit = 60.0
    detector.speed_estimation_enabled = True
    detector.enable_tracking = True
    detector.track_speeds = {1: 50.0}  # Vehicle going 50 km/h
    
    detections = [
        {'box': (100, 100, 200, 200), 'class_name': 'car', 'track_id': 1}
    ]
    
    violations = detector.detect_violations(detections)
    
    assert len(violations) == 0


@pytest.mark.violation_detection
@pytest.mark.unit
def test_add_violation_callback():
    """Test adding violation callback"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.violation_callbacks = []
    
    test_callback = lambda x: None
    detector.add_violation_callback(test_callback)
    
    assert len(detector.violation_callbacks) == 1
    assert test_callback in detector.violation_callbacks


@pytest.mark.violation_detection
@pytest.mark.unit
def test_violation_callback_triggered():
    """Test that violation callback is triggered"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.violation_detection_enabled = True
    detector.speed_limit = 60.0
    detector.speed_estimation_enabled = True
    detector.enable_tracking = True
    detector.track_speeds = {1: 80.0}
    detector.violation_callbacks = []
    detector.detected_violations = []
    
    callback_triggered = [False]
    
    def test_callback(violation):
        callback_triggered[0] = True
    
    detector.add_violation_callback(test_callback)
    
    detections = [
        {'box': (100, 100, 200, 200), 'class_name': 'car', 'track_id': 1}
    ]
    
    detector.detect_violations(detections)
    
    assert callback_triggered[0] is True


@pytest.mark.violation_detection
@pytest.mark.unit
def test_violation_recorded():
    """Test that violations are recorded"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.violation_detection_enabled = True
    detector.speed_limit = 60.0
    detector.speed_estimation_enabled = True
    detector.enable_tracking = True
    detector.track_speeds = {1: 80.0}
    detector.violation_callbacks = []
    detector.detected_violations = []
    
    detections = [
        {'box': (100, 100, 200, 200), 'class_name': 'car', 'track_id': 1}
    ]
    
    detector.detect_violations(detections)
    
    assert len(detector.detected_violations) == 1
    assert detector.detected_violations[0]['type'] == 'speeding'


@pytest.mark.violation_detection
@pytest.mark.unit
def test_multiple_violations():
    """Test detection of multiple violations"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.violation_detection_enabled = True
    detector.speed_limit = 60.0
    detector.speed_estimation_enabled = True
    detector.enable_tracking = True
    detector.track_speeds = {1: 80.0, 2: 90.0, 3: 55.0}  # Two speeding, one within limit
    detector.violation_callbacks = []
    detector.detected_violations = []
    
    detections = [
        {'box': (100, 100, 200, 200), 'class_name': 'car', 'track_id': 1},
        {'box': (200, 200, 300, 300), 'class_name': 'car', 'track_id': 2},
        {'box': (300, 300, 400, 400), 'class_name': 'car', 'track_id': 3}
    ]
    
    violations = detector.detect_violations(detections)
    
    assert len(violations) == 2


@pytest.mark.violation_detection
@pytest.mark.unit
def test_violation_without_tracking():
    """Test that violations require tracking to be enabled"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.violation_detection_enabled = True
    detector.speed_limit = 60.0
    detector.speed_estimation_enabled = False  # Disabled
    detector.enable_tracking = False  # Disabled
    
    detections = [
        {'box': (100, 100, 200, 200), 'class_name': 'car'}
    ]
    
    violations = detector.detect_violations(detections)
    
    assert len(violations) == 0
