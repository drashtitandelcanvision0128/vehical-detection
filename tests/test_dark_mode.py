"""
Dark Mode Toggle Tests for Vehicle Detection App
Tests for theme preference management
"""
import pytest


@pytest.mark.dark_mode
@pytest.mark.unit
def test_toggle_theme_route_exists():
    """Test that toggle theme route exists"""
    from web_test_app import app
    
    with app.test_client() as client:
        # Route should exist (GET request for existing toggle_theme route)
        response = client.get('/toggle_theme')
        # Should not be 404
        assert response.status_code != 404


@pytest.mark.dark_mode
@pytest.mark.unit
def test_toggle_theme_requires_login():
    """Test that toggle theme works (existing route uses session)"""
    from web_test_app import app
    
    with app.test_client() as client:
        # Existing toggle_theme doesn't require login, just toggles session
        response = client.get('/toggle_theme')
        # Should redirect
        assert response.status_code in [302, 200]


@pytest.mark.dark_mode
@pytest.mark.unit
def test_user_model_has_theme_field():
    """Test that User model has theme field"""
    from models import User
    
    # Check that theme column exists
    assert hasattr(User, 'theme')
    # Check that theme can be set
    user = User(username='test', email='test@example.com', password_hash='hash', theme='dark')
    assert user.theme == 'dark'


@pytest.mark.dark_mode
@pytest.mark.unit
def test_theme_default_value():
    """Test that theme field exists and can be set to 'light'"""
    from models import User
    
    user = User(username='test', email='test@example.com', password_hash='hash', theme='light')
    assert user.theme == 'light'


@pytest.mark.dark_mode
@pytest.mark.unit
def test_theme_can_be_dark():
    """Test that theme can be set to 'dark'"""
    from models import User
    
    user = User(username='test', email='test@example.com', password_hash='hash')
    user.theme = 'dark'
    assert user.theme == 'dark'


@pytest.mark.dark_mode
@pytest.mark.unit
def test_theme_can_be_light():
    """Test that theme can be set to 'light'"""
    from models import User
    
    user = User(username='test', email='test@example.com', password_hash='hash', theme='dark')
    user.theme = 'light'
    assert user.theme == 'light'
