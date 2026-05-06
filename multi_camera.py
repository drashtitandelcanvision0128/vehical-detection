"""
Multi-Camera Support for Vehicle Detection
Manages multiple camera sources with simultaneous detection
"""
import threading
import queue
import numpy as np
from vehicle_detector import VehicleDetector
from typing import List, Dict, Tuple, Optional
import cv2


class MultiCameraDetector:
    """
    Manage multiple camera sources with simultaneous vehicle detection
    """
    
    def __init__(self, model_path: str, num_cameras: int = 2, **detector_kwargs):
        """
        Initialize multi-camera detector
        
        Args:
            model_path: Path to YOLO model
            num_cameras: Number of camera sources
            **detector_kwargs: Arguments to pass to VehicleDetector instances
        """
        self.model_path = model_path
        self.num_cameras = num_cameras
        self.detectors: List[VehicleDetector] = []
        self.frames: Dict[int, np.ndarray] = {}
        self.detections: Dict[int, list] = {}
        self.running = False
        self.threads: List[threading.Thread] = []
        self.frame_queues: Dict[int, queue.Queue] = {}
        self.result_queues: Dict[int, queue.Queue] = {}
        
        # Initialize detectors for each camera
        for i in range(num_cameras):
            detector = VehicleDetector(model_path, **detector_kwargs)
            self.detectors.append(detector)
            self.frame_queues[i] = queue.Queue(maxsize=1)
            self.result_queues[i] = queue.Queue(maxsize=1)
        
        print(f"[INFO] MultiCameraDetector initialized with {num_cameras} cameras")
    
    def start(self, sources: List):
        """
        Start processing multiple camera sources
        
        Args:
            sources: List of camera sources (e.g., [0, 1] for webcams, ['video1.mp4', 'video2.mp4'])
        """
        if len(sources) != self.num_cameras:
            raise ValueError(f"Expected {self.num_cameras} sources, got {len(sources)}")
        
        self.running = True
        self.threads = []
        
        for i, source in enumerate(sources):
            thread = threading.Thread(
                target=self._process_camera,
                args=(i, source),
                daemon=True
            )
            thread.start()
            self.threads.append(thread)
            print(f"[INFO] Started camera {i} with source: {source}")
    
    def stop(self):
        """Stop all camera processing"""
        self.running = False
        for thread in self.threads:
            thread.join(timeout=2.0)
        print("[INFO] Stopped all cameras")
    
    def _process_camera(self, camera_id: int, source):
        """
        Process frames from a single camera
        
        Args:
            camera_id: Camera identifier
            source: Camera source (device index or file path)
        """
        cap = cv2.VideoCapture(source)
        
        if not cap.isOpened():
            print(f"[ERROR] Could not open camera {camera_id} with source {source}")
            return
        
        while self.running:
            ret, frame = cap.read()
            if not ret:
                print(f"[WARNING] Camera {camera_id} reached end of stream")
                break
            
            # Get latest frame (non-blocking)
            try:
                self.frame_queues[camera_id].get_nowait()  # Clear old frame
            except queue.Empty:
                pass
            
            self.frame_queues[camera_id].put(frame)
            
            # Run detection
            annotated_frame, detections = self.detectors[camera_id].detect(frame)
            
            # Get latest result (non-blocking)
            try:
                self.result_queues[camera_id].get_nowait()  # Clear old result
            except queue.Empty:
                pass
            
            self.result_queues[camera_id].put((annotated_frame, detections))
        
        cap.release()
    
    def get_frame(self, camera_id: int) -> Optional[np.ndarray]:
        """
        Get the latest frame from a camera
        
        Args:
            camera_id: Camera identifier
            
        Returns:
            Frame or None if no frame available
        """
        try:
            return self.frame_queues[camera_id].get_nowait()
        except (queue.Empty, KeyError):
            return None
    
    def get_detections(self, camera_id: int) -> Optional[Tuple[np.ndarray, list]]:
        """
        Get the latest detection result from a camera
        
        Args:
            camera_id: Camera identifier
            
        Returns:
            Tuple of (annotated_frame, detections) or None if no result available
        """
        try:
            return self.result_queues[camera_id].get_nowait()
        except (queue.Empty, KeyError):
            return None
    
    def get_all_frames(self) -> Dict[int, np.ndarray]:
        """
        Get latest frames from all cameras
        
        Returns:
            Dictionary mapping camera_id to frame
        """
        frames = {}
        for camera_id in range(self.num_cameras):
            frame = self.get_frame(camera_id)
            if frame is not None:
                frames[camera_id] = frame
        return frames
    
    def get_all_detections(self) -> Dict[int, Tuple[np.ndarray, list]]:
        """
        Get latest detection results from all cameras
        
        Returns:
            Dictionary mapping camera_id to (annotated_frame, detections)
        """
        results = {}
        for camera_id in range(self.num_cameras):
            result = self.get_detections(camera_id)
            if result is not None:
                results[camera_id] = result
        return results
    
    def is_running(self) -> bool:
        """Check if multi-camera processing is running"""
        return self.running
    
    def get_camera_count(self) -> int:
        """Get number of cameras"""
        return self.num_cameras
    
    def get_detector(self, camera_id: int) -> Optional[VehicleDetector]:
        """
        Get detector instance for a specific camera
        
        Args:
            camera_id: Camera identifier
            
        Returns:
            VehicleDetector instance or None if invalid camera_id
        """
        if 0 <= camera_id < len(self.detectors):
            return self.detectors[camera_id]
        return None


def create_grid_view(frames: Dict[int, np.ndarray], rows: int = 2, cols: int = 2) -> np.ndarray:
    """
    Create a grid view of multiple camera frames
    
    Args:
        frames: Dictionary mapping camera_id to frame
        rows: Number of rows in grid
        cols: Number of columns in grid
        
    Returns:
        Combined grid frame
    """
    if not frames:
        return np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Get frame size from first available frame
    first_frame = next(iter(frames.values()))
    frame_height, frame_width = first_frame.shape[:2]
    
    # Create blank grid
    grid = np.zeros((frame_height * rows, frame_width * cols, 3), dtype=np.uint8)
    
    # Place frames in grid
    for camera_id, frame in frames.items():
        if camera_id >= rows * cols:
            continue  # Skip if too many frames for grid
        
        row = camera_id // cols
        col = camera_id % cols
        
        # Resize frame to match grid cell size
        frame_resized = cv2.resize(frame, (frame_width, frame_height))
        
        y_start = row * frame_height
        y_end = y_start + frame_height
        x_start = col * frame_width
        x_end = x_start + frame_width
        
        grid[y_start:y_end, x_start:x_end] = frame_resized
        
        # Add camera label
        cv2.putText(
            grid, f"Camera {camera_id}", (x_start + 10, y_start + 30),
            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2
        )
    
    return grid
