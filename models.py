from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    """User model for future authentication"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Integer, default=1)

    # Relationships
    image_detections = relationship("ImageDetection", back_populates="user")
    video_detections = relationship("VideoDetection", back_populates="user")
    live_detections = relationship("LiveDetection", back_populates="user")


class ImageDetection(Base):
    """Model for image-based vehicle detection results"""
    __tablename__ = 'image_detections'

    id = Column(Integer, primary_key=True)
    report_id = Column(String(50), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    message = Column(Text)
    vehicle_count = Column(Integer, default=0)
    processing_time = Column(String(50))
    confidence_threshold = Column(Float)
    image_data = Column(Text)  # Base64 encoded image
    stats = Column(JSON)  # Detection statistics as JSON
    breakdown = Column(Text)  # Vehicle breakdown text

    # Relationship
    user = relationship("User", back_populates="image_detections")


class VideoDetection(Base):
    """Model for video-based vehicle detection results"""
    __tablename__ = 'video_detections'

    id = Column(Integer, primary_key=True)
    report_id = Column(String(50), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    message = Column(Text)
    vehicle_count = Column(Integer, default=0)
    processing_time = Column(String(50))
    confidence_threshold = Column(Float)
    video_path = Column(String(255))
    stats = Column(JSON)  # Detection statistics as JSON
    breakdown = Column(Text)  # Vehicle breakdown text

    # Relationship
    user = relationship("User", back_populates="video_detections")


class LiveDetection(Base):
    """Model for live webcam vehicle detection results"""
    __tablename__ = 'live_detections'

    id = Column(Integer, primary_key=True)
    report_id = Column(String(50), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    session_start = Column(DateTime)
    session_end = Column(DateTime)
    total_detections = Column(Integer, default=0)
    confidence_threshold = Column(Float, default=0.4)
    stats = Column(JSON)  # Detection statistics as JSON
    breakdown = Column(Text)  # Vehicle breakdown text

    # Relationship
    user = relationship("User", back_populates="live_detections")


class DetectionHistory(Base):
    """Simplified unified history table for all detection types - stores only report data"""
    __tablename__ = 'detection_history'

    id = Column(Integer, primary_key=True)
    report_id = Column(String(50), unique=True, nullable=False)
    detection_type = Column(String(20), nullable=False)  # 'image', 'video', 'live'
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Essential report data only (what's shown in PDF)
    vehicle_count = Column(Integer, default=0)
    processing_time = Column(String(50))
    confidence_threshold = Column(Float)
    breakdown = Column(Text)  # Vehicle breakdown as simple text
    
    # Optional preview data
    image_data = Column(Text, nullable=True)  # Base64 encoded image (for preview)
    video_path = Column(String(255), nullable=True)  # Video path (for video detections)
    
    # Relationship
    user = relationship("User", backref="detection_history")
