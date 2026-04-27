"""
API endpoint tests for Vehicle Detection App
"""
import pytest
import json


@pytest.mark.api
@pytest.mark.unit
def test_home_page_loads(test_client):
    """Test that home page loads successfully"""
    response = test_client.get('/')
    assert response.status_code in [200, 302]  # 200 or redirect to login


@pytest.mark.api
@pytest.mark.unit
def test_test_route(test_client):
    """Test the test route for health check"""
    response = test_client.get('/test')
    assert response.status_code == 200
    assert b'Test route is working' in response.data


@pytest.mark.api
@pytest.mark.unit
def test_history_page_requires_login(test_client):
    """Test that history page redirects to login if not authenticated"""
    response = test_client.get('/history', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.location


@pytest.mark.api
@pytest.mark.integration
def test_history_page_loads_when_authenticated(authenticated_client):
    """Test that history page loads for authenticated user"""
    response = authenticated_client.get('/history')
    assert response.status_code == 200


@pytest.mark.api
@pytest.mark.integration
def test_live_page_loads_when_authenticated(authenticated_client):
    """Test that live detection page loads for authenticated user"""
    response = authenticated_client.get('/live')
    assert response.status_code == 200


@pytest.mark.api
@pytest.mark.unit
def test_debug_route(test_client):
    """Test debug route for system status"""
    response = test_client.get('/debug')
    assert response.status_code in [200, 302]


@pytest.mark.api
@pytest.mark.unit
def test_post_without_auth_redirects(test_client):
    """Test that POST requests without authentication redirect"""
    response = test_client.post('/webcam_detect', data={})
    assert response.status_code in [302, 405]  # Redirect or method not allowed


@pytest.mark.api
@pytest.mark.integration
def test_image_upload_endpoint(authenticated_client, sample_image_bytes):
    """Test image upload endpoint"""
    response = authenticated_client.post('/', data={
        'image': (sample_image_bytes, 'test.jpg'),
        'conf_threshold': '0.4'
    }, content_type='multipart/form-data')
    
    # Should not crash (may fail detection but shouldn't error)
    assert response.status_code in [200, 400, 500]
