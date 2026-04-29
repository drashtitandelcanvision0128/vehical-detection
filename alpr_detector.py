"""
ALPR (Automatic License Plate Recognition) Module
Uses fast-alpr library for number plate detection and OCR
"""

import cv2
import numpy as np
import statistics
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
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image to improve ALPR detection quality
        - Denoising to reduce blur
        - Sharpening to enhance edges
        - Contrast enhancement
        
        Args:
            image: Input image (BGR format)
            
        Returns:
            Preprocessed image
        """
        # Denoising
        denoised = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
        
        # Sharpening using kernel
        sharpen_kernel = np.array([[-1, -1, -1],
                                   [-1,  9, -1],
                                   [-1, -1, -1]])
        sharpened = cv2.filter2D(denoised, -1, sharpen_kernel)
        
        # Contrast enhancement using CLAHE
        lab = cv2.cvtColor(sharpened, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        return enhanced
    
    def detect_plates(self, image: np.ndarray, preprocess: bool = False) -> list:
        """
        Detect license plates in an image
        
        Args:
            image: Input image (BGR format)
            preprocess: Whether to preprocess image before detection (default False,
                ALPR models are trained on raw images)
            
        Returns:
            List of detected plates with text and confidence
            Format: [{'text': str, 'confidence': float, 'detection_confidence': float,
                     'bbox': (x1, y1, x2, y2), 'region': str, 'region_confidence': float}]
        """
        if self.alpr is None:
            print("[ERROR] ALPR not initialized")
            return []
        
        try:
            # Optionally preprocess image for better detection
            input_image = self._preprocess_image(image) if preprocess else image
            
            # Run ALPR prediction
            results = self.alpr.predict(input_image)
            
            plates = []
            for result in results:
                detection = result.detection
                ocr = result.ocr
                
                if ocr is not None and ocr.text:
                    bbox = detection.bounding_box
                    confidence = (
                        statistics.mean(ocr.confidence)
                        if isinstance(ocr.confidence, list)
                        else ocr.confidence
                    )
                    
                    plates.append({
                        'text': ocr.text,
                        'confidence': float(confidence),
                        'detection_confidence': float(detection.confidence),
                        'bbox': (int(bbox.x1), int(bbox.y1), int(bbox.x2), int(bbox.y2)),
                        'region': ocr.region if ocr.region else None,
                        'region_confidence': float(ocr.region_confidence) if ocr.region_confidence is not None else None
                    })
            
            return plates
            
        except Exception as e:
            print(f"[ERROR] ALPR detection failed: {e}")
            return []
    
    def detect_and_draw(self, image: np.ndarray, preprocess: bool = False) -> tuple:
        """
        Detect plates and draw bounding boxes on image using ALPR's draw_predictions
        for high-quality annotations with proper font scaling, outlines, and region display.
        
        Args:
            image: Input image (BGR format)
            preprocess: Whether to preprocess image before detection
            
        Returns:
            Tuple of (annotated_image, plates_list)
        """
        if self.alpr is None:
            print("[ERROR] ALPR not initialized")
            return image.copy(), []
        
        try:
            # Use ALPR's draw_predictions for professional annotations
            # It handles font scaling, text outlines, region display, multi-line labels
            drawn = self.alpr.draw_predictions(image)
            annotated_image = drawn.image
            
            # Convert ALPR results to plates dict list for compatibility
            plates = []
            for result in drawn.results:
                detection = result.detection
                ocr = result.ocr
                
                if ocr is not None and ocr.text:
                    bbox = detection.bounding_box
                    confidence = (
                        statistics.mean(ocr.confidence)
                        if isinstance(ocr.confidence, list)
                        else ocr.confidence
                    )
                    
                    plates.append({
                        'text': ocr.text,
                        'confidence': float(confidence),
                        'detection_confidence': float(detection.confidence),
                        'bbox': (int(bbox.x1), int(bbox.y1), int(bbox.x2), int(bbox.y2)),
                        'region': ocr.region if ocr.region else None,
                        'region_confidence': float(ocr.region_confidence) if ocr.region_confidence is not None else None
                    })
            
            return annotated_image, plates
            
        except Exception as e:
            print(f"[ERROR] ALPR detect_and_draw failed: {e}")
            return image.copy(), []
    
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
            
            # Pass raw image to detect_plates (ALPR models trained on raw images)
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
