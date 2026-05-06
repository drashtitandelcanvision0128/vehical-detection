"""
Multi-Camera Support Tests for Vehicle Detection App
Tests for simultaneous multi-camera vehicle detection
"""
import pytest
import threading
import time
import numpy as np
from unittest.mock import MagicMock, patch


@pytest.mark.multi_camera
@pytest.mark.unit
def test_multi_camera_detector_initialization():
    """Test that MultiCameraDetector initializes correctly"""
    with patch('multi_camera.VehicleDetector') as mock_detector_class:
        mock_detector = MagicMock()
        mock_detector_class.return_value = mock_detector
        
        from multi_camera import MultiCameraDetector
        
        detector = MultiCameraDetector('yolov8n.pt', num_cameras=3)
        
        assert detector.num_cameras == 3
        assert len(detector.detectors) == 3
        assert len(detector.frame_queues) == 3
        assert len(detector.result_queues) == 3


@pytest.mark.multi_camera
@pytest.mark.unit
def test_multi_camera_detector_start_stop():
    """Test starting and stopping multi-camera processing"""
    with patch('multi_camera.VehicleDetector') as mock_detector_class:
        mock_detector = MagicMock()
        mock_detector.detect = MagicMock(return_value=(np.zeros((100, 100, 3), dtype=np.uint8), []))
        mock_detector_class.return_value = mock_detector
        
        from multi_camera import MultiCameraDetector
        
        detector = MultiCameraDetector('yolov8n.pt', num_cameras=2)
        
        # Mock cv2.VideoCapture
        with patch('multi_camera.cv2.VideoCapture') as mock_capture_class:
            mock_cap = MagicMock()
            mock_cap.isOpened.return_value = True
            mock_cap.read.return_value = (True, np.zeros((100, 100, 3), dtype=np.uint8))
            mock_capture_class.return_value = mock_cap
            
            detector.start([0, 1])
            assert detector.is_running() is True
            
            # Give threads time to start
            time.sleep(0.1)
            
            detector.stop()
            assert detector.is_running() is False


@pytest.mark.multi_camera
@pytest.mark.unit
def test_get_frame():
    """Test getting frame from specific camera"""
    with patch('multi_camera.VehicleDetector') as mock_detector_class:
        mock_detector = MagicMock()
        mock_detector_class.return_value = mock_detector
        
        from multi_camera import MultiCameraDetector
        
        detector = MultiCameraDetector('yolov8n.pt', num_cameras=2)
        
        test_frame = np.zeros((100, 100, 3), dtype=np.uint8)
        detector.frame_queues[0].put(test_frame)
        
        retrieved_frame = detector.get_frame(0)
        assert np.array_equal(retrieved_frame, test_frame)
        
        # Test non-existent camera
        assert detector.get_frame(5) is None


@pytest.mark.multi_camera
@pytest.mark.unit
def test_get_detections():
    """Test getting detections from specific camera"""
    with patch('multi_camera.VehicleDetector') as mock_detector_class:
        mock_detector = MagicMock()
        mock_detector_class.return_value = mock_detector
        
        from multi_camera import MultiCameraDetector
        
        detector = MultiCameraDetector('yolov8n.pt', num_cameras=2)
        
        test_frame = np.zeros((100, 100, 3), dtype=np.uint8)
        test_detections = [{'class_name': 'car', 'confidence': 0.95}]
        detector.result_queues[0].put((test_frame, test_detections))
        
        retrieved = detector.get_detections(0)
        assert retrieved is not None
        assert np.array_equal(retrieved[0], test_frame)
        assert retrieved[1] == test_detections


@pytest.mark.multi_camera
@pytest.mark.unit
def test_get_all_frames():
    """Test getting frames from all cameras"""
    with patch('multi_camera.VehicleDetector') as mock_detector_class:
        mock_detector = MagicMock()
        mock_detector_class.return_value = mock_detector
        
        from multi_camera import MultiCameraDetector
        
        detector = MultiCameraDetector('yolov8n.pt', num_cameras=3)
        
        detector.frame_queues[0].put(np.zeros((100, 100, 3), dtype=np.uint8))
        detector.frame_queues[1].put(np.zeros((100, 100, 3), dtype=np.uint8))
        detector.frame_queues[2].put(np.zeros((100, 100, 3), dtype=np.uint8))
        
        all_frames = detector.get_all_frames()
        assert len(all_frames) == 3


@pytest.mark.multi_camera
@pytest.mark.unit
def test_get_all_detections():
    """Test getting detections from all cameras"""
    with patch('multi_camera.VehicleDetector') as mock_detector_class:
        mock_detector = MagicMock()
        mock_detector_class.return_value = mock_detector
        
        from multi_camera import MultiCameraDetector
        
        detector = MultiCameraDetector('yolov8n.pt', num_cameras=2)
        
        detector.result_queues[0].put((np.zeros((100, 100, 3), dtype=np.uint8), []))
        detector.result_queues[1].put((np.zeros((100, 100, 3), dtype=np.uint8), []))
        
        all_detections = detector.get_all_detections()
        assert len(all_detections) == 2


@pytest.mark.multi_camera
@pytest.mark.unit
def test_get_detector():
    """Test getting detector for specific camera"""
    with patch('multi_camera.VehicleDetector') as mock_detector_class:
        mock_detector = MagicMock()
        mock_detector_class.return_value = mock_detector
        
        from multi_camera import MultiCameraDetector
        
        detector = MultiCameraDetector('yolov8n.pt', num_cameras=3)
        
        # Valid camera ID
        retrieved = detector.get_detector(0)
        assert retrieved is not None
        
        # Invalid camera ID
        retrieved = detector.get_detector(5)
        assert retrieved is None


@pytest.mark.multi_camera
@pytest.mark.unit
def test_start_with_wrong_source_count():
    """Test that start raises error with wrong number of sources"""
    with patch('multi_camera.VehicleDetector') as mock_detector_class:
        mock_detector = MagicMock()
        mock_detector_class.return_value = mock_detector
        
        from multi_camera import MultiCameraDetector
        
        detector = MultiCameraDetector('yolov8n.pt', num_cameras=3)
        
        # Try to start with only 2 sources instead of 3
        with pytest.raises(ValueError):
            detector.start([0, 1])


@pytest.mark.multi_camera
@pytest.mark.unit
def test_create_grid_view():
    """Test creating a grid view of multiple frames"""
    from multi_camera import create_grid_view
    import cv2
    
    frames = {
        0: np.zeros((100, 100, 3), dtype=np.uint8),
        1: np.zeros((100, 100, 3), dtype=np.uint8),
        2: np.zeros((100, 100, 3), dtype=np.uint8),
        3: np.zeros((100, 100, 3), dtype=np.uint8),
    }
    
    grid = create_grid_view(frames, rows=2, cols=2)
    
    assert grid.shape == (200, 200, 3)  # 2 rows * 100 height, 2 cols * 100 width


@pytest.mark.multi_camera
@pytest.mark.unit
def test_create_grid_view_empty():
    """Test creating grid view with no frames"""
    from multi_camera import create_grid_view
    
    grid = create_grid_view({}, rows=2, cols=2)
    
    assert grid.shape == (480, 640, 3)  # Default size


@pytest.mark.multi_camera
@pytest.mark.unit
def test_create_grid_view_partial_frames():
    """Test creating grid view with partial frames"""
    from multi_camera import create_grid_view
    
    frames = {
        0: np.zeros((100, 100, 3), dtype=np.uint8),
        2: np.zeros((100, 100, 3), dtype=np.uint8),
    }
    
    grid = create_grid_view(frames, rows=2, cols=2)
    
    assert grid.shape == (200, 200, 3)
    # Should have frames at positions 0 and 2


@pytest.mark.multi_camera
@pytest.mark.unit
def test_camera_count():
    """Test getting camera count"""
    with patch('multi_camera.VehicleDetector') as mock_detector_class:
        mock_detector = MagicMock()
        mock_detector_class.return_value = mock_detector
        
        from multi_camera import MultiCameraDetector
        
        detector = MultiCameraDetector('yolov8n.pt', num_cameras=4)
        
        assert detector.get_camera_count() == 4
