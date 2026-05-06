"""
Heatmap Visualization Tests for Vehicle Detection App
Tests for traffic density heatmap visualization
"""
import pytest
import numpy as np
from collections import defaultdict


@pytest.mark.heatmap
@pytest.mark.unit
def test_enable_heatmap():
    """Test that enable_heatmap properly initializes heatmap state"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.heatmap_enabled = False
    detector.heatmap_accumulator = None
    detector.heatmap_frame_size = None
    detector.heatmap_alpha = 0.6
    detector.heatmap_colormap = 2  # cv2.COLORMAP_JET
    
    detector.enable_heatmap(frame_size=(640, 480), alpha=0.7)
    
    assert detector.heatmap_enabled is True
    assert detector.heatmap_alpha == 0.7
    assert detector.heatmap_frame_size == (640, 480)
    assert detector.heatmap_accumulator is not None
    assert detector.heatmap_accumulator.shape == (480, 640)


@pytest.mark.heatmap
@pytest.mark.unit
def test_disable_heatmap():
    """Test that disable_heatmap clears heatmap state"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.heatmap_enabled = True
    detector.heatmap_accumulator = np.zeros((480, 640), dtype=np.float32)
    
    detector.disable_heatmap()
    
    assert detector.heatmap_enabled is False
    assert detector.heatmap_accumulator is None


@pytest.mark.heatmap
@pytest.mark.unit
def test_clear_heatmap():
    """Test that clear_heatmap resets accumulator to zeros"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.heatmap_enabled = True
    detector.heatmap_accumulator = np.ones((480, 640), dtype=np.float32) * 100
    
    detector.clear_heatmap()
    
    assert np.all(detector.heatmap_accumulator == 0)


@pytest.mark.heatmap
@pytest.mark.unit
def test_update_heatmap():
    """Test that update_heatmap adds vehicle positions to accumulator"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.heatmap_enabled = True
    detector.heatmap_accumulator = np.zeros((480, 640), dtype=np.float32)
    detector.heatmap_frame_size = (640, 480)
    
    detections = [
        {'box': (100, 100, 200, 200), 'class_id': 2, 'conf': 0.9, 'class_name': 'car'},
        {'box': (300, 300, 400, 400), 'class_id': 3, 'conf': 0.8, 'class_name': 'motorcycle'},
    ]
    
    detector.update_heatmap(detections, (640, 480))
    
    # Check that some values in the accumulator are now > 0
    assert detector.heatmap_accumulator.max() > 0


@pytest.mark.heatmap
@pytest.mark.unit
def test_update_heatmap_disabled():
    """Test that update_heatmap does nothing when disabled"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.heatmap_enabled = False
    detector.heatmap_accumulator = None
    
    detections = [{'box': (100, 100, 200, 200), 'class_id': 2, 'conf': 0.9, 'class_name': 'car'}]
    
    detector.update_heatmap(detections, (640, 480))
    
    assert detector.heatmap_accumulator is None


@pytest.mark.heatmap
@pytest.mark.unit
def test_update_heatmap_initializes_on_first_frame():
    """Test that update_heatmap initializes accumulator on first frame"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.heatmap_enabled = True
    detector.heatmap_accumulator = None
    
    detections = [{'box': (100, 100, 200, 200), 'class_id': 2, 'conf': 0.9, 'class_name': 'car'}]
    
    detector.update_heatmap(detections, (640, 480))
    
    assert detector.heatmap_accumulator is not None
    assert detector.heatmap_accumulator.shape == (480, 640)
    assert detector.heatmap_frame_size == (640, 480)


@pytest.mark.heatmap
@pytest.mark.unit
def test_update_heatmap_resizes_on_frame_change():
    """Test that update_heatmap resizes accumulator when frame size changes"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.heatmap_enabled = True
    detector.heatmap_accumulator = np.zeros((480, 640), dtype=np.float32)
    detector.heatmap_frame_size = (640, 480)
    
    detections = [{'box': (100, 100, 200, 200), 'class_id': 2, 'conf': 0.9, 'class_name': 'car'}]
    
    # Update with different frame size
    detector.update_heatmap(detections, (1280, 720))
    
    assert detector.heatmap_accumulator.shape == (720, 1280)
    assert detector.heatmap_frame_size == (1280, 720)


@pytest.mark.heatmap
@pytest.mark.unit
def test_draw_heatmap():
    """Test that draw_heatmap overlays heatmap on frame"""
    from vehicle_detector import VehicleDetector
    import cv2
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.heatmap_enabled = True
    detector.heatmap_accumulator = np.zeros((480, 640), dtype=np.float32)
    detector.heatmap_alpha = 0.6
    detector.heatmap_colormap = cv2.COLORMAP_JET
    
    # Add some data to heatmap
    detector.heatmap_accumulator[200:280, 100:200] = 50.0
    
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    frame[:] = [100, 100, 100]  # Gray background
    
    result = detector.draw_heatmap(frame)
    
    assert result.shape == frame.shape
    # Result should be different from original due to overlay
    assert not np.array_equal(result, frame)


@pytest.mark.heatmap
@pytest.mark.unit
def test_draw_heatmap_disabled():
    """Test that draw_heatmap returns original frame when disabled"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.heatmap_enabled = False
    detector.heatmap_accumulator = None
    
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    result = detector.draw_heatmap(frame)
    
    assert np.array_equal(result, frame)


@pytest.mark.heatmap
@pytest.mark.unit
def test_draw_heatmap_no_accumulator():
    """Test that draw_heatmap returns original frame when accumulator is None"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.heatmap_enabled = True
    detector.heatmap_accumulator = None
    
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    result = detector.draw_heatmap(frame)
    
    assert np.array_equal(result, frame)


@pytest.mark.heatmap
@pytest.mark.unit
def test_heatmap_alpha_clamping():
    """Test that heatmap alpha is clamped between 0 and 1"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.heatmap_enabled = False
    detector.heatmap_accumulator = None
    detector.heatmap_alpha = 0.6
    
    # Test with alpha > 1
    detector.enable_heatmap(frame_size=(640, 480), alpha=1.5)
    assert detector.heatmap_alpha == 1.0
    
    # Test with alpha < 0
    detector.enable_heatmap(frame_size=(640, 480), alpha=-0.5)
    assert detector.heatmap_alpha == 0.0


@pytest.mark.heatmap
@pytest.mark.unit
def test_heatmap_accumulation_over_frames():
    """Test that heatmap accumulates data over multiple frames"""
    from vehicle_detector import VehicleDetector
    
    detector = VehicleDetector.__new__(VehicleDetector)
    detector.heatmap_enabled = True
    detector.heatmap_accumulator = np.zeros((480, 640), dtype=np.float32)
    detector.heatmap_frame_size = (640, 480)
    
    # Frame 1
    detections1 = [{'box': (100, 100, 200, 200), 'class_id': 2, 'conf': 0.9, 'class_name': 'car'}]
    detector.update_heatmap(detections1, (640, 480))
    max1 = detector.heatmap_accumulator.max()
    
    # Frame 2 - same location
    detections2 = [{'box': (105, 105, 205, 205), 'class_id': 2, 'conf': 0.9, 'class_name': 'car'}]
    detector.update_heatmap(detections2, (640, 480))
    max2 = detector.heatmap_accumulator.max()
    
    # Max value should increase due to accumulation
    assert max2 >= max1
