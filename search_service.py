"""
Search and Filter Service for Vehicle Detection App
Handles advanced search and filtering of detection history
"""
from datetime import datetime, timedelta
from sqlalchemy import and_, or_


class SearchService:
    """Service for searching and filtering detection history"""
    
    def __init__(self, db_session):
        """
        Initialize search service
        
        Args:
            db_session: Database session
        """
        self.db = db_session
    
    def search_detections(self, user_id=None, filters=None):
        """
        Search detections with filters
        
        Args:
            user_id: User ID (optional, for user-specific searches)
            filters: Dictionary of filters
                - date_from: Start date (YYYY-MM-DD)
                - date_to: End date (YYYY-MM-DD)
                - detection_type: Type (image, video, live)
                - min_vehicles: Minimum vehicle count
                - max_vehicles: Maximum vehicle count
                - vehicle_type: Specific vehicle type (car, motorcycle, bus, truck)
                - search_text: Text search in message/breakdown
                - limit: Maximum results
                - offset: Pagination offset
        
        Returns:
            List of detection records
        """
        from models import DetectionHistory
        
        filters = filters or {}
        query = self.db.query(DetectionHistory)
        
        # Filter by user if provided
        if user_id:
            query = query.filter(DetectionHistory.user_id == user_id)
        
        # Date range filter
        if filters.get('date_from'):
            try:
                date_from = datetime.strptime(filters['date_from'], '%Y-%m-%d')
                query = query.filter(DetectionHistory.timestamp >= date_from)
            except ValueError:
                pass
        
        if filters.get('date_to'):
            try:
                date_to = datetime.strptime(filters['date_to'], '%Y-%m-%d')
                # Include end date
                date_to = date_to + timedelta(days=1)
                query = query.filter(DetectionHistory.timestamp < date_to)
            except ValueError:
                pass
        
        # Detection type filter
        if filters.get('detection_type'):
            query = query.filter(DetectionHistory.detection_type == filters['detection_type'])
        
        # Vehicle count range filter
        if filters.get('min_vehicles'):
            try:
                min_vehicles = int(filters['min_vehicles'])
                query = query.filter(DetectionHistory.vehicle_count >= min_vehicles)
            except ValueError:
                pass
        
        if filters.get('max_vehicles'):
            try:
                max_vehicles = int(filters['max_vehicles'])
                query = query.filter(DetectionHistory.vehicle_count <= max_vehicles)
            except ValueError:
                pass
        
        # Text search filter
        if filters.get('search_text'):
            search_text = f"%{filters['search_text']}%"
            query = query.filter(
                or_(
                    DetectionHistory.message.like(search_text),
                    DetectionHistory.breakdown.like(search_text)
                )
            )
        
        # Vehicle type specific filter (in breakdown)
        if filters.get('vehicle_type'):
            vehicle_type = filters['vehicle_type']
            query = query.filter(DetectionHistory.breakdown.like(f"%{vehicle_type}%"))
        
        # Order by timestamp (newest first)
        query = query.order_by(DetectionHistory.timestamp.desc())
        
        # Pagination
        limit = filters.get('limit', 50)
        offset = filters.get('offset', 0)
        
        try:
            limit = int(limit)
            offset = int(offset)
        except ValueError:
            limit = 50
            offset = 0
        
        query = query.limit(limit).offset(offset)
        
        # Execute query
        results = query.all()
        
        # Convert to dictionary format
        detections = []
        for d in results:
            detections.append({
                'id': d.id,
                'report_id': d.report_id,
                'detection_type': d.detection_type,
                'timestamp': d.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'vehicle_count': d.vehicle_count or 0,
                'processing_time': d.processing_time,
                'confidence_threshold': d.confidence_threshold,
                'breakdown': d.breakdown,
                'message': d.message,
                'user_id': d.user_id
            })
        
        return detections
    
    def get_filter_stats(self, user_id=None):
        """
        Get statistics for filter options
        
        Args:
            user_id: User ID (optional)
        
        Returns:
            Dictionary with filter statistics
        """
        from models import DetectionHistory
        
        query = self.db.query(DetectionHistory)
        
        if user_id:
            query = query.filter(DetectionHistory.user_id == user_id)
        
        detections = query.all()
        
        # Detection type counts
        type_counts = {'image': 0, 'video': 0, 'live': 0}
        for d in detections:
            if d.detection_type in type_counts:
                type_counts[d.detection_type] += 1
        
        # Vehicle count range
        vehicle_counts = [d.vehicle_count or 0 for d in detections]
        min_vehicles = min(vehicle_counts) if vehicle_counts else 0
        max_vehicles = max(vehicle_counts) if vehicle_counts else 0
        
        # Date range
        timestamps = [d.timestamp for d in detections if d.timestamp]
        if timestamps:
            min_date = min(timestamps).strftime('%Y-%m-%d')
            max_date = max(timestamps).strftime('%Y-%m-%d')
        else:
            min_date = None
            max_date = None
        
        return {
            'total_detections': len(detections),
            'type_counts': type_counts,
            'vehicle_range': {
                'min': min_vehicles,
                'max': max_vehicles
            },
            'date_range': {
                'min': min_date,
                'max': max_date
            }
        }
