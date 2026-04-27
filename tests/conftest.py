"""
Pytest fixtures and configuration for Vehicle Detection App tests
"""
import pytest
import os
import sys
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask
from werkzeug.security import generate_password_hash
from models import Base, User, ImageDetection, DetectionHistory
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope="session")
def test_db_url():
    """Provide test database URL"""
    return "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_db(test_db_url):
    """Create a fresh database for each test"""
    engine = create_engine(test_db_url)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    
    db = SessionLocal()
    yield db
    
    db.close()
    engine.dispose()


@pytest.fixture(scope="function")
def test_user(test_db):
    """Create a test user"""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=generate_password_hash("testpass123"),
        is_active=1
    )
    test_db.add(user)
    test_db.commit()
    return user


@pytest.fixture(scope="function")
def test_client(test_db):
    """Create a test Flask client"""
    # Import after database is set up
    from web_test_app import app, init_db
    
    # Override database with test database
    import web_test_app as app_module
    app_module.engine = test_db.get_bind()
    app_module.SessionLocal = sessionmaker(bind=app_module.engine)
    
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        yield client


@pytest.fixture(scope="function")
def authenticated_client(test_client, test_user):
    """Create an authenticated test client"""
    with test_client.session_transaction() as sess:
        sess['user_id'] = test_user.id
        sess['username'] = test_user.username
    return test_client


@pytest.fixture
def sample_image():
    """Provide a sample image for testing"""
    # Create a simple test image (1x1 pixel black image)
    import numpy as np
    import cv2
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    return img


@pytest.fixture
def sample_image_bytes(sample_image):
    """Convert sample image to bytes"""
    import cv2
    _, buffer = cv2.imencode('.jpg', sample_image)
    return buffer.tobytes()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for file operations"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def mock_model():
    """Mock YOLO model for testing without actual model"""
    from unittest.mock import MagicMock
    
    mock_result = MagicMock()
    mock_result.boxes = MagicMock()
    mock_result.boxes.__iter__ = MagicMock(return_value=iter([]))
    mock_result.boxes.cpu = MagicMock()
    
    mock_predict = MagicMock()
    mock_predict.predict = MagicMock(return_value=[mock_result])
    
    return mock_predict
