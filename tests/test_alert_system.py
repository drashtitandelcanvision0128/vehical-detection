"""
Alert System Tests for Vehicle Detection App
Tests for threshold-based real-time alerts
"""
import pytest
from collections import defaultdict
from unittest.mock import MagicMock, patch


@pytest.mark.alert
@pytest.mark.unit
def test_alert_system_enabled_by_default():
    """Test that alert system is enabled by default"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.alert_system_enabled = True
    detector.speed_threshold = 60.0
    detector.vehicle_count_threshold = 5
    detector.alert_callbacks = []
    detector.active_alerts = set()
    detector.alert_cooldown = 30
    detector.alert_cooldowns = {}
    
    assert detector.alert_system_enabled is True
    assert detector.speed_threshold == 60.0
    assert detector.vehicle_count_threshold == 5


@pytest.mark.alert
@pytest.mark.unit
def test_set_speed_threshold():
    """Test setting speed threshold for alerts"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.speed_threshold = 60.0
    
    detector.set_speed_threshold(80.0)
    assert detector.speed_threshold == 80.0


@pytest.mark.alert
@pytest.mark.unit
def test_set_vehicle_count_threshold():
    """Test setting vehicle count threshold for alerts"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.vehicle_count_threshold = 5
    
    detector.set_vehicle_count_threshold(10)
    assert detector.vehicle_count_threshold == 10


@pytest.mark.alert
@pytest.mark.unit
def test_add_alert_callback():
    """Test adding alert callback"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.alert_callbacks = []
    
    mock_callback = MagicMock()
    detector.add_alert_callback(mock_callback)
    
    assert len(detector.alert_callbacks) == 1
    assert mock_callback in detector.alert_callbacks


@pytest.mark.alert
@pytest.mark.unit
def test_speed_exceeded_alert():
    """Test that speed exceeding threshold triggers alert"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.alert_system_enabled = True
    detector.speed_estimation_enabled = True
    detector.enable_tracking = True
    detector.speed_threshold = 60.0
    detector.vehicle_count_threshold = 5
    detector.alert_callbacks = []
    detector.active_alerts = set()
    detector.alert_cooldown = 30
    detector.alert_cooldowns = {}
    detector.track_speeds = {1: 70.0}  # Vehicle at 70 km/h (exceeds 60)
    
    detections = [
        {'box': (100, 100, 200, 200), 'class_id': 2, 'conf': 0.9, 'class_name': 'car', 'track_id': 1},
    ]
    
    alerts = detector.check_alerts(detections)
    
    assert len(alerts) == 1
    assert alerts[0]['type'] == 'speed_exceeded'
    assert alerts[0]['speed'] == 70.0
    assert alerts[0]['threshold'] == 60.0


@pytest.mark.alert
@pytest.mark.unit
def test_speed_below_threshold_no_alert():
    """Test that speed below threshold does not trigger alert"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.alert_system_enabled = True
    detector.speed_estimation_enabled = True
    detector.enable_tracking = True
    detector.speed_threshold = 60.0
    detector.vehicle_count_threshold = 5
    detector.alert_callbacks = []
    detector.active_alerts = set()
    detector.alert_cooldown = 30
    detector.alert_cooldowns = {}
    detector.track_speeds = {1: 50.0}  # Vehicle at 50 km/h (below 60)
    
    detections = [
        {'box': (100, 100, 200, 200), 'class_id': 2, 'conf': 0.9, 'class_name': 'car', 'track_id': 1},
    ]
    
    alerts = detector.check_alerts(detections)
    
    assert len(alerts) == 0


@pytest.mark.alert
@pytest.mark.unit
def test_vehicle_count_exceeded_alert():
    """Test that vehicle count exceeding threshold triggers alert"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.alert_system_enabled = True
    detector.speed_estimation_enabled = True
    detector.enable_tracking = True
    detector.vehicle_count_threshold = 5
    detector.alert_callbacks = []
    detector.active_alerts = set()
    detector.alert_cooldown = 30
    detector.alert_cooldowns = {}
    detector.track_speeds = {}
    
    # 6 vehicles (exceeds threshold of 5)
    detections = [
        {'box': (100, 100, 200, 200), 'class_id': 2, 'conf': 0.9, 'class_name': 'car', 'track_id': 1},
        {'box': (300, 100, 400, 200), 'class_id': 3, 'conf': 0.8, 'class_name': 'motorcycle', 'track_id': 2},
        {'box': (500, 100, 600, 200), 'class_id': 2, 'conf': 0.85, 'class_name': 'car', 'track_id': 3},
        {'box': (700, 100, 800, 200), 'class_id': 5, 'conf': 0.9, 'class_name': 'bus', 'track_id': 4},
        {'box': (900, 100, 1000, 200), 'class_id': 7, 'conf': 0.8, 'class_name': 'truck', 'track_id': 5},
        {'box': (1100, 100, 1200, 200), 'class_id': 2, 'conf': 0.75, 'class_name': 'car', 'track_id': 6},
    ]
    
    alerts = detector.check_alerts(detections)
    
    assert len(alerts) == 1
    assert alerts[0]['type'] == 'count_exceeded'
    assert alerts[0]['count'] == 6
    assert alerts[0]['threshold'] == 5


@pytest.mark.alert
@pytest.mark.unit
def test_vehicle_count_below_threshold_no_alert():
    """Test that vehicle count below threshold does not trigger alert"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.alert_system_enabled = True
    detector.speed_estimation_enabled = True
    detector.enable_tracking = True
    detector.vehicle_count_threshold = 10
    detector.alert_callbacks = []
    detector.active_alerts = set()
    detector.alert_cooldown = 30
    detector.alert_cooldowns = {}
    detector.track_speeds = {}
    
    # 5 vehicles (below threshold of 10)
    detections = [
        {'box': (100, 100, 200, 200), 'class_id': 2, 'conf': 0.9, 'class_name': 'car', 'track_id': 1},
        {'box': (300, 100, 400, 200), 'class_id': 3, 'conf': 0.8, 'class_name': 'motorcycle', 'track_id': 2},
        {'box': (500, 100, 600, 200), 'class_id': 2, 'conf': 0.85, 'class_name': 'car', 'track_id': 3},
        {'box': (700, 100, 800, 200), 'class_id': 5, 'conf': 0.9, 'class_name': 'bus', 'track_id': 4},
        {'box': (900, 100, 1000, 200), 'class_id': 7, 'conf': 0.8, 'class_name': 'truck', 'track_id': 5},
    ]
    
    alerts = detector.check_alerts(detections)
    
    assert len(alerts) == 0


@pytest.mark.alert
@pytest.mark.unit
def test_alert_cooldown():
    """Test that alerts have cooldown period to prevent spam"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.alert_system_enabled = True
    detector.speed_estimation_enabled = True
    detector.enable_tracking = True
    detector.speed_threshold = 60.0
    detector.vehicle_count_threshold = 5
    detector.alert_callbacks = []
    detector.active_alerts = set()
    detector.alert_cooldown = 2  # Short cooldown for testing
    detector.alert_cooldowns = {}
    detector.track_speeds = {1: 70.0}
    
    detections = [
        {'box': (100, 100, 200, 200), 'class_id': 2, 'conf': 0.9, 'class_name': 'car', 'track_id': 1},
    ]
    
    # First check - should trigger
    alerts = detector.check_alerts(detections)
    assert len(alerts) == 1
    
    # Second check - should not trigger (cooldown active)
    alerts = detector.check_alerts(detections)
    assert len(alerts) == 0
    
    # Third check - cooldown expired
    detector.alert_cooldowns = {}  # Manually expire
    alerts = detector.check_alerts(detections)
    assert len(alerts) == 1


@pytest.mark.alert
@pytest.mark.unit
def test_alert_callback_triggered():
    """Test that alert callback is called when alert triggers"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.alert_system_enabled = True
    detector.speed_estimation_enabled = True
    detector.enable_tracking = True
    detector.speed_threshold = 60.0
    detector.vehicle_count_threshold = 5
    detector.alert_callbacks = []
    detector.active_alerts = set()
    detector.alert_cooldown = 30
    detector.alert_cooldowns = {}
    detector.track_speeds = {1: 70.0}
    
    mock_callback = MagicMock()
    detector.add_alert_callback(mock_callback)
    
    detections = [
        {'box': (100, 100, 200, 200), 'class_id': 2, 'conf': 0.9, 'class_name': 'car', 'track_id': 1},
    ]
    
    detector.check_alerts(detections)
    
    # Callback should have been called once
    assert mock_callback.call_count == 1
    # Verify the alert data was passed correctly
    alert_arg = mock_callback.call_args[0][0]
    assert alert_arg['type'] == 'speed_exceeded'
    assert alert_arg['speed'] == 70.0


@pytest.mark.alert
@pytest.mark.unit
def test_alert_system_disabled():
    """Test that no alerts trigger when system is disabled"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.alert_system_enabled = False
    detector.speed_estimation_enabled = True
    detector.enable_tracking = True
    detector.speed_threshold = 60.0
    detector.track_speeds = {1: 70.0}
    
    detections = [
        {'box': (100, 100, 200, 200), 'class_id': 2, 'conf': 0.9, 'class_name': 'car', 'track_id': 1},
    ]
    
    alerts = detector.check_alerts(detections)
    
    assert len(alerts) == 0


@pytest.mark.alert
@pytest.mark.unit
def test_multiple_alerts_triggered():
    """Test that multiple different alerts can trigger simultaneously"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.alert_system_enabled = True
    detector.speed_estimation_enabled = True
    detector.enable_tracking = True
    detector.speed_threshold = 60.0
    detector.vehicle_count_threshold = 2
    detector.alert_callbacks = []
    detector.active_alerts = set()
    detector.alert_cooldown = 30
    detector.alert_cooldowns = {}
    detector.track_speeds = {1: 70.0, 2: 80.0}  # Both exceeding speed
    
    # 3 vehicles (exceeds count threshold of 2)
    detections = [
        {'box': (100, 100, 200, 200), 'class_id': 2, 'conf': 0.9, 'class_name': 'car', 'track_id': 1},
        {'box': (300, 100, 400, 200), 'class_id': 3, 'conf': 0.8, 'class_name': 'motorcycle', 'track_id': 2},
        {'box': (500, 100, 600, 200), 'class_id': 2, 'conf': 0.85, 'class_name': 'car', 'track_id': 3},
    ]
    
    alerts = detector.check_alerts(detections)
    
    # Should trigger 3 alerts: 2 speed alerts + 1 count alert
    assert len(alerts) == 3
    alert_types = [a['type'] for a in alerts]
    assert alert_types.count('speed_exceeded') == 2
    assert alert_types.count('count_exceeded') == 1
