"""
Authentication tests for Vehicle Detection App
"""
import pytest
from flask import session


@pytest.mark.auth
@pytest.mark.unit
def test_login_page_loads(test_client):
    """Test that login page loads successfully"""
    response = test_client.get('/login')
    assert response.status_code == 200
    assert b'Login' in response.data


@pytest.mark.auth
@pytest.mark.unit
def test_register_page_loads(test_client):
    """Test that register page loads successfully"""
    response = test_client.get('/register')
    assert response.status_code == 200
    assert b'Register' in response.data


@pytest.mark.auth
@pytest.mark.unit
def test_user_registration(test_client, test_db):
    """Test user registration with valid data"""
    response = test_client.post('/register', data={
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    # Check if user was created in database
    from models import User
    user = test_db.query(User).filter(User.username == 'newuser').first()
    assert user is not None
    assert user.email == 'newuser@example.com'


@pytest.mark.auth
@pytest.mark.unit
def test_user_registration_password_mismatch(test_client):
    """Test registration fails with password mismatch"""
    response = test_client.post('/register', data={
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'password123',
        'confirm_password': 'different123'
    })
    
    assert response.status_code == 200
    assert b'Passwords do not match' in response.data


@pytest.mark.auth
@pytest.mark.unit
def test_user_registration_short_password(test_client):
    """Test registration fails with short password"""
    response = test_client.post('/register', data={
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': '123',
        'confirm_password': '123'
    })
    
    assert response.status_code == 200
    assert b'Password must be at least 6 characters' in response.data


@pytest.mark.auth
@pytest.mark.unit
def test_user_registration_missing_fields(test_client):
    """Test registration fails with missing fields"""
    response = test_client.post('/register', data={
        'username': 'newuser',
        'email': '',
        'password': 'password123',
        'confirm_password': 'password123'
    })
    
    assert response.status_code == 200
    assert b'All fields are required' in response.data


@pytest.mark.auth
@pytest.mark.unit
def test_user_login_success(test_client, test_user):
    """Test successful login with valid credentials"""
    response = test_client.post('/login', data={
        'username': test_user.username,
        'password': 'testpass123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Login successful' in response.data


@pytest.mark.auth
@pytest.mark.unit
def test_user_login_invalid_credentials(test_client, test_user):
    """Test login fails with invalid credentials"""
    response = test_client.post('/login', data={
        'username': test_user.username,
        'password': 'wrongpassword'
    })
    
    assert response.status_code == 200
    assert b'Invalid username or password' in response.data


@pytest.mark.auth
@pytest.mark.unit
def test_logout(authenticated_client):
    """Test logout functionality"""
    response = authenticated_client.get('/logout', follow_redirects=True)
    
    assert response.status_code == 200
    assert b'logged out' in response.data


@pytest.mark.auth
@pytest.mark.unit
def test_already_logged_in_redirects_to_index(authenticated_client):
    """Test that logged-in user is redirected from login page"""
    response = authenticated_client.get('/login', follow_redirects=False)
    assert response.status_code == 302  # Redirect
    assert '/' in response.location
