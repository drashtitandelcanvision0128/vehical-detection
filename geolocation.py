"""
Geolocation Manager for Vehicle Detection App
Handles location data for detection events
"""
from typing import Optional, Tuple
import math


class GeolocationManager:
    """
    Manager for geolocation operations
    """
    
    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two coordinates in kilometers using Haversine formula
        
        Args:
            lat1, lon1: First coordinate
            lat2, lon2: Second coordinate
            
        Returns:
            Distance in kilometers
        """
        # Earth radius in kilometers
        R = 6371.0
        
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Differences
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        # Haversine formula
        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        distance = R * c
        return distance
    
    @staticmethod
    def validate_coordinates(latitude: float, longitude: float) -> bool:
        """
        Validate latitude and longitude coordinates
        
        Args:
            latitude: Latitude value
            longitude: Longitude value
            
        Returns:
            True if valid, False otherwise
        """
        # Latitude: -90 to 90
        # Longitude: -180 to 180
        return -90 <= latitude <= 90 and -180 <= longitude <= 180
    
    @staticmethod
    def format_coordinates(latitude: float, longitude: float) -> str:
        """
        Format coordinates as a string
        
        Args:
            latitude: Latitude value
            longitude: Longitude value
            
        Returns:
            Formatted coordinate string
        """
        return f"{latitude:.6f}, {longitude:.6f}"
    
    @staticmethod
    def parse_coordinates(coord_string: str) -> Optional[Tuple[float, float]]:
        """
        Parse coordinate string into latitude and longitude
        
        Args:
            coord_string: String in format "lat, lon"
            
        Returns:
            Tuple of (latitude, longitude) or None if invalid
        """
        try:
            parts = coord_string.split(',')
            if len(parts) != 2:
                return None
            
            lat = float(parts[0].strip())
            lon = float(parts[1].strip())
            
            if not GeolocationManager.validate_coordinates(lat, lon):
                return None
            
            return (lat, lon)
        except (ValueError, IndexError):
            return None
    
    @staticmethod
    def get_bounding_box(latitude: float, longitude: float, radius_km: float) -> Tuple[float, float, float, float]:
        """
        Get bounding box coordinates around a center point
        
        Args:
            latitude: Center latitude
            longitude: Center longitude
            radius_km: Radius in kilometers
            
        Returns:
            Tuple of (min_lat, max_lat, min_lon, max_lon)
        """
        # Approximate conversion: 1 degree lat ≈ 111 km
        # Longitude varies with latitude
        lat_delta = radius_km / 111.0
        lon_delta = radius_km / (111.0 * math.cos(math.radians(latitude)))
        
        min_lat = latitude - lat_delta
        max_lat = latitude + lat_delta
        min_lon = longitude - lon_delta
        max_lon = longitude + lon_delta
        
        return (min_lat, max_lat, min_lon, max_lon)
