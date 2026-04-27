"""
Database operations tests for Vehicle Detection App
"""
import pytest
from datetime import datetime
from models import User, ImageDetection, VideoDetection, DetectionHistory


@pytest.mark.unit
def test_create_user(test_db):
    """Test creating a new user in database"""
    user = User(
        username="dbtestuser",
        email="dbtest@example.com",
        password_hash="hashed_password",
        is_active=1
    )
    test_db.add(user)
    test_db.commit()
    
    retrieved_user = test_db.query(User).filter(User.username == "dbtestuser").first()
    assert retrieved_user is not None
    assert retrieved_user.email == "dbtest@example.com"


@pytest.mark.unit
def test_user_unique_constraint(test_db):
    """Test that username must be unique"""
    user1 = User(
        username="uniqueuser",
        email="user1@example.com",
        password_hash="hashed1",
        is_active=1
    )
    test_db.add(user1)
    test_db.commit()
    
    user2 = User(
        username="uniqueuser",  # Same username
        email="user2@example.com",
        password_hash="hashed2",
        is_active=1
    )
    test_db.add(user2)
    
    with pytest.raises(Exception):  # Should raise integrity error
        test_db.commit()


@pytest.mark.unit
def test_create_image_detection(test_db, test_user):
    """Test creating an image detection record"""
    detection = ImageDetection(
        report_id="test_report_001",
        user_id=test_user.id,
        timestamp=datetime.utcnow(),
        message="Test detection",
        vehicle_count=5,
        processing_time="1.23s",
        confidence_threshold=0.4,
        image_data="base64_image_data",
        stats={"count": 5, "time": 1.23},
        breakdown="Car: 3, Truck: 2"
    )
    test_db.add(detection)
    test_db.commit()
    
    retrieved = test_db.query(ImageDetection).filter_by(report_id="test_report_001").first()
    assert retrieved is not None
    assert retrieved.vehicle_count == 5
    assert retrieved.user_id == test_user.id


@pytest.mark.unit
def test_create_detection_history(test_db, test_user):
    """Test creating detection history record"""
    history = DetectionHistory(
        report_id="history_001",
        detection_type="image",
        user_id=test_user.id,
        timestamp=datetime.utcnow(),
        vehicle_count=3,
        processing_time="0.5s",
        confidence_threshold=0.4,
        breakdown="Car: 2, Motorcycle: 1"
    )
    test_db.add(history)
    test_db.commit()
    
    retrieved = test_db.query(DetectionHistory).filter_by(report_id="history_001").first()
    assert retrieved is not None
    assert retrieved.detection_type == "image"
    assert retrieved.vehicle_count == 3


@pytest.mark.unit
def test_user_detection_relationship(test_db, test_user):
    """Test relationship between user and detections"""
    detection = ImageDetection(
        report_id="rel_test_001",
        user_id=test_user.id,
        timestamp=datetime.utcnow(),
        message="Test",
        vehicle_count=1,
        processing_time="0.1s",
        confidence_threshold=0.4,
        image_data="data",
        stats={"count": 1},
        breakdown="Car: 1"
    )
    test_db.add(detection)
    test_db.commit()
    
    # Test forward relationship (user -> detections)
    user_detections = test_user.image_detections
    assert len(user_detections) == 1
    assert user_detections[0].report_id == "rel_test_001"
    
    # Test backward relationship (detection -> user)
    retrieved_detection = test_db.query(ImageDetection).first()
    assert retrieved_detection.user.username == test_user.username


@pytest.mark.unit
def test_update_detection_record(test_db, test_user):
    """Test updating an existing detection record"""
    detection = ImageDetection(
        report_id="update_test_001",
        user_id=test_user.id,
        timestamp=datetime.utcnow(),
        message="Original message",
        vehicle_count=2,
        processing_time="0.3s",
        confidence_threshold=0.4,
        image_data="data",
        stats={"count": 2},
        breakdown="Car: 2"
    )
    test_db.add(detection)
    test_db.commit()
    
    # Update
    detection.vehicle_count = 5
    detection.message = "Updated message"
    test_db.commit()
    
    retrieved = test_db.query(ImageDetection).filter_by(report_id="update_test_001").first()
    assert retrieved.vehicle_count == 5
    assert retrieved.message == "Updated message"


@pytest.mark.unit
def test_delete_detection_record(test_db, test_user):
    """Test deleting a detection record"""
    detection = ImageDetection(
        report_id="delete_test_001",
        user_id=test_user.id,
        timestamp=datetime.utcnow(),
        message="To be deleted",
        vehicle_count=1,
        processing_time="0.1s",
        confidence_threshold=0.4,
        image_data="data",
        stats={"count": 1},
        breakdown="Car: 1"
    )
    test_db.add(detection)
    test_db.commit()
    
    # Delete
    test_db.delete(detection)
    test_db.commit()
    
    retrieved = test_db.query(ImageDetection).filter_by(report_id="delete_test_001").first()
    assert retrieved is None
