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
    # Flash message "Login successful!" is rendered in the redirected index page
    assert b'successful' in response.data or b'Welcome' in response.data


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


# ===== Forgot Password Tests =====

@pytest.mark.auth
@pytest.mark.unit
def test_forgot_password_page_loads(test_client):
    """Test that forgot password page loads successfully"""
    response = test_client.get('/forgot-password')
    assert response.status_code == 200
    assert b'Forgot Password' in response.data


@pytest.mark.auth
@pytest.mark.unit
def test_forgot_password_with_existing_email(test_client, test_user):
    """Test forgot password with an email that exists in the system"""
    response = test_client.post('/forgot-password', data={
        'email': test_user.email
    }, follow_redirects=True)
    
    assert response.status_code == 200
    # Should show reset link (email not configured in test mode)
    assert b'Reset link' in response.data or b'reset link' in response.data or b'sent' in response.data


@pytest.mark.auth
@pytest.mark.unit
def test_forgot_password_with_nonexistent_email(test_client):
    """Test forgot password with an email that doesn't exist - should not reveal info"""
    response = test_client.post('/forgot-password', data={
        'email': 'nonexistent@example.com'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    # Should show generic message, not reveal email doesn't exist
    assert b'reset link has been sent' in response.data or b'account with that email' in response.data


@pytest.mark.auth
@pytest.mark.unit
def test_forgot_password_generates_token(test_client, test_user, test_db):
    """Test that forgot password generates a reset token in the database"""
    from models import User
    
    response = test_client.post('/forgot-password', data={
        'email': test_user.email
    }, follow_redirects=True)
    
    assert response.status_code == 200
    
    # Expire the session cache to see changes made by the web app's separate session
    test_db.expire_all()
    user = test_db.query(User).filter(User.email == test_user.email).first()
    assert user is not None
    assert user.reset_token is not None
    assert user.reset_token_expires is not None


@pytest.mark.auth
@pytest.mark.unit
def test_reset_password_page_with_valid_token(test_client, test_user, test_db):
    """Test that reset password page loads with a valid token"""
    from models import User
    import secrets
    from datetime import datetime, timedelta
    
    # Generate a token manually
    token = secrets.token_urlsafe(32)
    test_user.reset_token = token
    test_user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
    test_db.commit()
    
    response = test_client.get(f'/reset-password/{token}')
    assert response.status_code == 200
    assert b'Reset Password' in response.data


@pytest.mark.auth
@pytest.mark.unit
def test_reset_password_with_invalid_token(test_client):
    """Test reset password with an invalid token"""
    response = test_client.get('/reset-password/invalidtoken123', follow_redirects=True)
    assert response.status_code == 200
    assert b'Invalid or expired' in response.data


@pytest.mark.auth
@pytest.mark.unit
def test_reset_password_with_expired_token(test_client, test_user, test_db):
    """Test reset password with an expired token"""
    from models import User
    from datetime import datetime, timedelta
    
    # Generate an expired token
    test_user.reset_token = 'expiredtesttoken'
    test_user.reset_token_expires = datetime.utcnow() - timedelta(hours=1)  # Expired
    test_db.commit()
    
    response = test_client.get('/reset-password/expiredtesttoken', follow_redirects=True)
    assert response.status_code == 200
    assert b'expired' in response.data or b'Expired' in response.data


@pytest.mark.auth
@pytest.mark.unit
def test_reset_password_success(test_client, test_user, test_db):
    """Test successful password reset"""
    from models import User
    import secrets
    from datetime import datetime, timedelta
    
    # Generate a valid token
    token = secrets.token_urlsafe(32)
    test_user.reset_token = token
    test_user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
    test_db.commit()
    
    # Reset password
    response = test_client.post(f'/reset-password/{token}', data={
        'new_password': 'newpassword456',
        'confirm_password': 'newpassword456'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'reset successfully' in response.data or b'successfully' in response.data
    
    # Verify password was changed - expire session cache first
    test_db.expire_all()
    user = test_db.query(User).filter(User.email == test_user.email).first()
    assert user.reset_token is None  # Token should be cleared
    assert user.reset_token_expires is None
    
    # Verify can login with new password
    response = test_client.post('/login', data={
        'username': test_user.username,
        'password': 'newpassword456'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'successful' in response.data or b'Welcome' in response.data


@pytest.mark.auth
@pytest.mark.unit
def test_reset_password_mismatch(test_client, test_user, test_db):
    """Test reset password fails when passwords don't match"""
    from secrets import token_urlsafe
    from datetime import datetime, timedelta
    
    token = token_urlsafe(32)
    test_user.reset_token = token
    test_user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
    test_db.commit()
    
    response = test_client.post(f'/reset-password/{token}', data={
        'new_password': 'newpassword456',
        'confirm_password': 'different789'
    })
    
    assert response.status_code == 200
    assert b'do not match' in response.data


@pytest.mark.auth
@pytest.mark.unit
def test_reset_password_too_short(test_client, test_user, test_db):
    """Test reset password fails when password is too short"""
    from secrets import token_urlsafe
    from datetime import datetime, timedelta
    
    token = token_urlsafe(32)
    test_user.reset_token = token
    test_user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
    test_db.commit()
    
    response = test_client.post(f'/reset-password/{token}', data={
        'new_password': '123',
        'confirm_password': '123'
    })
    
    assert response.status_code == 200
    assert b'at least 6 characters' in response.data
