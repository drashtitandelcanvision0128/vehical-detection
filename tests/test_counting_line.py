"""
Counting Line Tests for Vehicle Detection App
Tests for zone-based vehicle counting via virtual counting line
"""
import pytest
from collections import defaultdict
from unittest.mock import MagicMock, patch


@pytest.mark.counting
@pytest.mark.unit
def test_set_counting_line():
    """Test that set_counting_line properly configures the counting line"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.counting_line = None
    detector.counting_line_enabled = False
    detector.counted_track_ids = set()
    detector.line_crossing_counts = defaultdict(int)
    detector.total_line_crossings = 0
    detector.counting_direction = 'both'
    
    detector.set_counting_line((0, 300), (640, 300), direction='down')
    
    assert detector.counting_line == ((0, 300), (640, 300))
    assert detector.counting_line_enabled is True
    assert detector.counting_direction == 'down'
    assert detector.total_line_crossings == 0


@pytest.mark.counting
@pytest.mark.unit
def test_clear_counting_line():
    """Test that clear_counting_line resets all counting state"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.counting_line = ((0, 300), (640, 300))
    detector.counting_line_enabled = True
    detector.counted_track_ids = {1, 2, 3}
    detector.line_crossing_counts = defaultdict(int, {'car': 2, 'bus': 1})
    detector.total_line_crossings = 3
    detector.counting_direction = 'both'
    
    detector.clear_counting_line()
    
    assert detector.counting_line is None
    assert detector.counting_line_enabled is False
    assert len(detector.counted_track_ids) == 0
    assert detector.total_line_crossings == 0


@pytest.mark.counting
@pytest.mark.unit
def test_segments_intersect_crossing():
    """Test that _segments_intersect detects a proper crossing"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    
    # Horizontal line from (0,300) to (640,300)
    # Vehicle moving from (100,280) to (100,320) - crosses the line
    result = detector._segments_intersect((100, 280), (100, 320), (0, 300), (640, 300))
    assert result is True


@pytest.mark.counting
@pytest.mark.unit
def test_segments_intersect_no_crossing():
    """Test that _segments_intersect returns False when no crossing"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    
    # Horizontal line from (0,300) to (640,300)
    # Vehicle moving from (100,280) to (100,290) - doesn't cross
    result = detector._segments_intersect((100, 280), (100, 290), (0, 300), (640, 300))
    assert result is False


@pytest.mark.counting
@pytest.mark.unit
def test_segments_intersect_parallel():
    """Test that parallel segments don't intersect"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    
    # Two parallel horizontal lines
    result = detector._segments_intersect((0, 280), (640, 280), (0, 300), (640, 300))
    assert result is False


@pytest.mark.counting
@pytest.mark.unit
def test_check_line_crossings_basic():
    """Test that check_line_crossings detects a vehicle crossing the line"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.counting_line = ((0, 300), (640, 300))
    detector.counting_line_enabled = True
    detector.enable_tracking = True
    detector.counted_track_ids = set()
    detector.line_crossing_counts = defaultdict(int)
    detector.total_line_crossings = 0
    detector.counting_direction = 'both'
    detector.track_history = defaultdict(list)
    
    # Simulate track history: vehicle was above line, now below
    detector.track_history[1] = [(100, 280), (100, 320)]
    
    detections = [
        {'box': (80, 300, 120, 340), 'class_id': 2, 'conf': 0.9, 'class_name': 'car', 'track_id': 1},
    ]
    
    crossed = detector.check_line_crossings(detections)
    
    assert len(crossed) == 1
    assert detector.total_line_crossings == 1
    assert detector.line_crossing_counts['car'] == 1
    assert 1 in detector.counted_track_ids


@pytest.mark.counting
@pytest.mark.unit
def test_check_line_crossings_no_double_count():
    """Test that same vehicle crossing line is not counted twice"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.counting_line = ((0, 300), (640, 300))
    detector.counting_line_enabled = True
    detector.enable_tracking = True
    detector.counted_track_ids = set()
    detector.line_crossing_counts = defaultdict(int)
    detector.total_line_crossings = 0
    detector.counting_direction = 'both'
    detector.track_history = defaultdict(list)
    
    # Frame 1: vehicle crosses line
    detector.track_history[1] = [(100, 280), (100, 320)]
    detections = [
        {'box': (80, 300, 120, 340), 'class_id': 2, 'conf': 0.9, 'class_name': 'car', 'track_id': 1},
    ]
    detector.check_line_crossings(detections)
    assert detector.total_line_crossings == 1
    
    # Frame 2: same vehicle still below line (should NOT be counted again)
    detector.track_history[1] = [(100, 280), (100, 320), (100, 330)]
    detections = [
        {'box': (80, 310, 120, 350), 'class_id': 2, 'conf': 0.9, 'class_name': 'car', 'track_id': 1},
    ]
    detector.check_line_crossings(detections)
    assert detector.total_line_crossings == 1  # Still 1, not 2


@pytest.mark.counting
@pytest.mark.unit
def test_check_line_crossings_direction_up():
    """Test that direction='up' only counts vehicles moving upward"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.counting_line = ((0, 300), (640, 300))
    detector.counting_line_enabled = True
    detector.enable_tracking = True
    detector.counted_track_ids = set()
    detector.line_crossing_counts = defaultdict(int)
    detector.total_line_crossings = 0
    detector.counting_direction = 'up'
    detector.track_history = defaultdict(list)
    
    # Vehicle moving upward (y decreases): (100,320) -> (100,280)
    detector.track_history[1] = [(100, 320), (100, 280)]
    detections = [
        {'box': (80, 260, 120, 300), 'class_id': 2, 'conf': 0.9, 'class_name': 'car', 'track_id': 1},
    ]
    crossed = detector.check_line_crossings(detections)
    assert len(crossed) == 1  # Should count upward movement
    
    # Vehicle moving downward (y increases): (200,280) -> (200,320)
    detector.track_history[2] = [(200, 280), (200, 320)]
    detections2 = [
        {'box': (180, 300, 220, 340), 'class_id': 3, 'conf': 0.8, 'class_name': 'motorcycle', 'track_id': 2},
    ]
    crossed2 = detector.check_line_crossings(detections2)
    assert len(crossed2) == 0  # Should NOT count downward movement


@pytest.mark.counting
@pytest.mark.unit
def test_check_line_crossings_direction_down():
    """Test that direction='down' only counts vehicles moving downward"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.counting_line = ((0, 300), (640, 300))
    detector.counting_line_enabled = True
    detector.enable_tracking = True
    detector.counted_track_ids = set()
    detector.line_crossing_counts = defaultdict(int)
    detector.total_line_crossings = 0
    detector.counting_direction = 'down'
    detector.track_history = defaultdict(list)
    
    # Vehicle moving downward (y increases): (100,280) -> (100,320)
    detector.track_history[1] = [(100, 280), (100, 320)]
    detections = [
        {'box': (80, 300, 120, 340), 'class_id': 2, 'conf': 0.9, 'class_name': 'car', 'track_id': 1},
    ]
    crossed = detector.check_line_crossings(detections)
    assert len(crossed) == 1  # Should count downward movement
    
    # Vehicle moving upward (y decreases): (200,320) -> (200,280)
    detector.track_history[2] = [(200, 320), (200, 280)]
    detections2 = [
        {'box': (180, 260, 220, 300), 'class_id': 3, 'conf': 0.8, 'class_name': 'motorcycle', 'track_id': 2},
    ]
    crossed2 = detector.check_line_crossings(detections2)
    assert len(crossed2) == 0  # Should NOT count upward movement


@pytest.mark.counting
@pytest.mark.unit
def test_check_line_crossings_disabled():
    """Test that check_line_crossings returns empty when disabled"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.counting_line_enabled = False
    detector.enable_tracking = True
    
    detections = [
        {'box': (80, 300, 120, 340), 'class_id': 2, 'conf': 0.9, 'class_name': 'car', 'track_id': 1},
    ]
    
    crossed = detector.check_line_crossings(detections)
    assert crossed == []


@pytest.mark.counting
@pytest.mark.unit
def test_check_line_crossings_no_tracking():
    """Test that check_line_crossings returns empty when tracking is disabled"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.counting_line = ((0, 300), (640, 300))
    detector.counting_line_enabled = True
    detector.enable_tracking = False
    
    detections = [
        {'box': (80, 300, 120, 340), 'class_id': 2, 'conf': 0.9, 'class_name': 'car', 'track_id': None},
    ]
    
    crossed = detector.check_line_crossings(detections)
    assert crossed == []


@pytest.mark.counting
@pytest.mark.unit
def test_multiple_vehicles_crossing():
    """Test counting multiple different vehicles crossing the line"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.counting_line = ((0, 300), (640, 300))
    detector.counting_line_enabled = True
    detector.enable_tracking = True
    detector.counted_track_ids = set()
    detector.line_crossing_counts = defaultdict(int)
    detector.total_line_crossings = 0
    detector.counting_direction = 'both'
    detector.track_history = defaultdict(list)
    
    # Car crossing
    detector.track_history[1] = [(100, 280), (100, 320)]
    # Bus crossing
    detector.track_history[2] = [(300, 280), (300, 320)]
    
    detections = [
        {'box': (80, 300, 120, 340), 'class_id': 2, 'conf': 0.9, 'class_name': 'car', 'track_id': 1},
        {'box': (280, 300, 350, 380), 'class_id': 5, 'conf': 0.85, 'class_name': 'bus', 'track_id': 2},
    ]
    
    crossed = detector.check_line_crossings(detections)
    assert len(crossed) == 2
    assert detector.total_line_crossings == 2
    assert detector.line_crossing_counts['car'] == 1
    assert detector.line_crossing_counts['bus'] == 1
