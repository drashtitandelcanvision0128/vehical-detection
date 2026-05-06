"""
Geolocation Tests for Vehicle Detection App
Tests for geolocation operations
"""
import pytest
import math


@pytest.mark.geolocation
@pytest.mark.unit
def test_calculate_distance():
    """Test distance calculation between two coordinates"""
    from geolocation import GeolocationManager
    
    # Distance between New York (40.7128, -74.0060) and Los Angeles (34.0522, -118.2437)
    # Should be approximately 3944 km
    distance = GeolocationManager.calculate_distance(40.7128, -74.0060, 34.0522, -118.2437)
    
    assert 3900 < distance < 4000  # Allow some tolerance


@pytest.mark.geolocation
@pytest.mark.unit
def test_calculate_distance_same_point():
    """Test distance calculation for same point"""
    from geolocation import GeolocationManager
    
    distance = GeolocationManager.calculate_distance(40.7128, -74.0060, 40.7128, -74.0060)
    
    assert distance == 0.0


@pytest.mark.geolocation
@pytest.mark.unit
def test_validate_coordinates_valid():
    """Test validation of valid coordinates"""
    from geolocation import GeolocationManager
    
    # Valid coordinates
    assert GeolocationManager.validate_coordinates(40.7128, -74.0060) is True
    assert GeolocationManager.validate_coordinates(0, 0) is True
    assert GeolocationManager.validate_coordinates(90, 180) is True
    assert GeolocationManager.validate_coordinates(-90, -180) is True


@pytest.mark.geolocation
@pytest.mark.unit
def test_validate_coordinates_invalid():
    """Test validation of invalid coordinates"""
    from geolocation import GeolocationManager
    
    # Invalid latitude
    assert GeolocationManager.validate_coordinates(91, 0) is False
    assert GeolocationManager.validate_coordinates(-91, 0) is False
    
    # Invalid longitude
    assert GeolocationManager.validate_coordinates(0, 181) is False
    assert GeolocationManager.validate_coordinates(0, -181) is False


@pytest.mark.geolocation
@pytest.mark.unit
def test_format_coordinates():
    """Test coordinate formatting"""
    from geolocation import GeolocationManager
    
    formatted = GeolocationManager.format_coordinates(40.7128, -74.0060)
    
    assert formatted == "40.712800, -74.006000"


@pytest.mark.geolocation
@pytest.mark.unit
def test_parse_coordinates_valid():
    """Test parsing valid coordinate string"""
    from geolocation import GeolocationManager
    
    coords = GeolocationManager.parse_coordinates("40.7128, -74.0060")
    
    assert coords is not None
    assert coords[0] == 40.7128
    assert coords[1] == -74.0060


@pytest.mark.geolocation
@pytest.mark.unit
def test_parse_coordinates_invalid_format():
    """Test parsing invalid coordinate string"""
    from geolocation import GeolocationManager
    
    # Invalid format
    assert GeolocationManager.parse_coordinates("invalid") is None
    assert GeolocationManager.parse_coordinates("40.7128") is None
    assert GeolocationManager.parse_coordinates("40.7128, -74.0060, extra") is None


@pytest.mark.geolocation
@pytest.mark.unit
def test_parse_coordinates_invalid_values():
    """Test parsing coordinate string with invalid values"""
    from geolocation import GeolocationManager
    
    # Invalid values
    assert GeolocationManager.parse_coordinates("91, 0") is None  # Invalid latitude
    assert GeolocationManager.parse_coordinates("0, 181") is None  # Invalid longitude


@pytest.mark.geolocation
@pytest.mark.unit
def test_get_bounding_box():
    """Test bounding box calculation"""
    from geolocation import GeolocationManager
    
    # 10 km radius around (40.7128, -74.0060)
    min_lat, max_lat, min_lon, max_lon = GeolocationManager.get_bounding_box(40.7128, -74.0060, 10)
    
    # Center should be in the middle
    assert min_lat < 40.7128 < max_lat
    assert min_lon < -74.0060 < max_lon
    
    # Box should be roughly symmetric
    assert abs((max_lat - min_lat) - 2 * (40.7128 - min_lat)) < 0.01


@pytest.mark.geolocation
@pytest.mark.unit
def test_models_have_geolocation_fields():
    """Test that detection models have geolocation fields"""
    from models import ImageDetection, VideoDetection, LiveDetection
    
    # Check ImageDetection
    assert hasattr(ImageDetection, 'latitude')
    assert hasattr(ImageDetection, 'longitude')
    
    # Check VideoDetection
    assert hasattr(VideoDetection, 'latitude')
    assert hasattr(VideoDetection, 'longitude')
    
    # Check LiveDetection
    assert hasattr(LiveDetection, 'latitude')
    assert hasattr(LiveDetection, 'longitude')
