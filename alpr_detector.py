"""
ALPR (Automatic License Plate Recognition) Module
Uses fast-alpr library for number plate detection and OCR
"""

import cv2
import numpy as np
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()


class ALPRDetector:
    """
    Wrapper for fast-alpr library to detect and recognize license plates
    """
    
    def __init__(self):
        """Initialize ALPR detector"""
        self.alpr = None
        self._initialize_alpr()
    
    def _initialize_alpr(self):
        """Initialize fast-alpr with default settings"""
        try:
            from fast_alpr import ALPR
            self.alpr = ALPR()
            print("[INFO] ALPR detector initialized successfully")
        except ImportError:
            print("[ERROR] fast-alpr not installed. Install with: pip install fast-alpr")
            self.alpr = None
        except Exception as e:
            print(f"[ERROR] Failed to initialize ALPR: {e}")
            self.alpr = None
    
    def detect_plates(self, image: np.ndarray) -> list:
        """
        Detect license plates in an image
        
        Args:
            image: Input image (BGR format)
            
        Returns:
            List of detected plates with text and confidence
            Format: [{'text': str, 'confidence': float, 'bbox': (x1, y1, x2, y2)}]
        """
        if self.alpr is None:
            print("[ERROR] ALPR not initialized")
            return []
        
        try:
            # Run ALPR prediction
            results = self.alpr.predict(image)
            
            plates = []
            for result in results:
                detection = result.detection
                ocr = result.ocr
                
                if ocr is not None and ocr.text:
                    bbox = detection.bounding_box
                    confidence = (
                        sum(ocr.confidence) / len(ocr.confidence)
                        if isinstance(ocr.confidence, list)
                        else ocr.confidence
                    )
                    
                    plates.append({
                        'text': ocr.text,
                        'confidence': float(confidence),
                        'bbox': (int(bbox.x1), int(bbox.y1), int(bbox.x2), int(bbox.y2)),
                        'region': ocr.region if ocr.region else None
                    })
            
            return plates
            
        except Exception as e:
            print(f"[ERROR] ALPR detection failed: {e}")
            return []
    
    def detect_and_draw(self, image: np.ndarray) -> tuple:
        """
        Detect plates and draw bounding boxes on image
        
        Args:
            image: Input image (BGR format)
            
        Returns:
            Tuple of (annotated_image, plates_list)
        """
        annotated = image.copy()
        plates = self.detect_plates(image)
        
        for plate in plates:
            x1, y1, x2, y2 = plate['bbox']
            text = plate['text']
            conf = plate['confidence']
            
            # Draw bounding box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Draw label
            label = f"{text} ({conf*100:.1f}%)"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            cv2.rectangle(annotated, (x1, y1 - label_size[1] - 10), 
                         (x1 + label_size[0], y1), (0, 255, 0), -1)
            cv2.putText(annotated, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
        
        return annotated, plates
    
    def detect_from_base64(self, base64_image: str) -> list:
        """
        Detect plates from base64 encoded image
        
        Args:
            base64_image: Base64 encoded image string
            
        Returns:
            List of detected plates
        """
        try:
            # Decode base64 image
            if ',' in base64_image:
                base64_image = base64_image.split(',')[1]
            
            img_data = base64.b64decode(base64_image)
            nparr = np.frombuffer(img_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                print("[ERROR] Failed to decode base64 image")
                return []
            
            return self.detect_plates(image)
            
        except Exception as e:
            print(f"[ERROR] Failed to process base64 image: {e}")
            return []


# Global instance
_alpr_detector = None


def get_alpr_detector():
    """Get or create global ALPR detector instance"""
    global _alpr_detector
    if _alpr_detector is None:
        _alpr_detector = ALPRDetector()
    return _alpr_detector
