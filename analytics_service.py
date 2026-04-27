"""
Analytics Service for Vehicle Detection App
Provides statistics and analytics for detection data
"""
from datetime import datetime, timedelta
from collections import defaultdict
import json


class AnalyticsService:
    """Service for computing analytics from detection data"""
    
    def __init__(self, db_session):
        """
        Initialize analytics service
        
        Args:
            db_session: Database session
        """
        self.db = db_session
    
    def get_overall_stats(self, days=30):
        """
        Get overall statistics for the specified time period
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dictionary with overall statistics
        """
        from models import DetectionHistory
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        detections = self.db.query(DetectionHistory).filter(
            DetectionHistory.timestamp >= cutoff_date
        ).all()
        
        if not detections:
            return {
                'total_detections': 0,
                'total_vehicles': 0,
                'avg_vehicles_per_detection': 0,
                'avg_processing_time': 0,
                'most_common_vehicle': 'N/A'
            }
        
        total_detections = len(detections)
        total_vehicles = sum(d.vehicle_count or 0 for d in detections)
        avg_vehicles = total_vehicles / total_detections if total_detections > 0 else 0
        
        # Calculate average processing time
        processing_times = []
        for d in detections:
            if d.processing_time:
                try:
                    time_val = float(d.processing_time.replace('s', ''))
                    processing_times.append(time_val)
                except:
                    pass
        
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        # Find most common vehicle type
        vehicle_counts = defaultdict(int)
        for d in detections:
            if d.breakdown:
                parts = d.breakdown.split(', ')
                for part in parts:
                    if ':' in part:
                        vehicle_type = part.split(':')[0].strip()
                        try:
                            count = int(part.split(':')[1].strip())
                            vehicle_counts[vehicle_type] += count
                        except:
                            pass
        
        most_common = max(vehicle_counts.items(), key=lambda x: x[1])[0] if vehicle_counts else 'N/A'
        
        return {
            'total_detections': total_detections,
            'total_vehicles': total_vehicles,
            'avg_vehicles_per_detection': round(avg_vehicles, 2),
            'avg_processing_time': round(avg_processing_time, 2),
            'most_common_vehicle': most_common
        }
    
    def get_detection_by_type(self, days=30):
        """
        Get detection counts by type (image, video, live)
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dictionary with counts by type
        """
        from models import DetectionHistory
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        detections = self.db.query(DetectionHistory).filter(
            DetectionHistory.timestamp >= cutoff_date
        ).all()
        
        type_counts = defaultdict(int)
        for d in detections:
            type_counts[d.detection_type] += 1
        
        return {
            'image': type_counts.get('image', 0),
            'video': type_counts.get('video', 0),
            'live': type_counts.get('live', 0)
        }
    
    def get_daily_trends(self, days=30):
        """
        Get daily detection trends
        
        Args:
            days: Number of days to analyze
        
        Returns:
            List of daily statistics
        """
        from models import DetectionHistory
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        detections = self.db.query(DetectionHistory).filter(
            DetectionHistory.timestamp >= cutoff_date
        ).all()
        
        # Group by date
        daily_stats = defaultdict(lambda: {'count': 0, 'vehicles': 0})
        
        for d in detections:
            date_key = d.timestamp.strftime('%Y-%m-%d')
            daily_stats[date_key]['count'] += 1
            daily_stats[date_key]['vehicles'] += (d.vehicle_count or 0)
        
        # Convert to sorted list
        result = []
        for date in sorted(daily_stats.keys()):
            result.append({
                'date': date,
                'detections': daily_stats[date]['count'],
                'vehicles': daily_stats[date]['vehicles']
            })
        
        return result
    
    def get_vehicle_breakdown(self, days=30):
        """
        Get breakdown of vehicle types detected
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dictionary with vehicle type counts
        """
        from models import DetectionHistory
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        detections = self.db.query(DetectionHistory).filter(
            DetectionHistory.timestamp >= cutoff_date
        ).all()
        
        vehicle_counts = defaultdict(int)
        
        for d in detections:
            if d.breakdown:
                parts = d.breakdown.split(', ')
                for part in parts:
                    if ':' in part:
                        vehicle_type = part.split(':')[0].strip()
                        try:
                            count = int(part.split(':')[1].strip())
                            vehicle_counts[vehicle_type] += count
                        except:
                            pass
        
        return dict(vehicle_counts)
    
    def get_hourly_distribution(self, days=7):
        """
        Get detection distribution by hour of day
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dictionary with hourly counts
        """
        from models import DetectionHistory
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        detections = self.db.query(DetectionHistory).filter(
            DetectionHistory.timestamp >= cutoff_date
        ).all()
        
        hourly_counts = defaultdict(int)
        
        for d in detections:
            hour = d.timestamp.hour
            hourly_counts[hour] += 1
        
        # Fill in all hours with 0 if no data
        result = []
        for hour in range(24):
            result.append({
                'hour': hour,
                'count': hourly_counts.get(hour, 0)
            })
        
        return result
    
    def get_user_activity(self, days=30, limit=10):
        """
        Get top users by detection count
        
        Args:
            days: Number of days to analyze
            limit: Number of users to return
        
        Returns:
            List of user activity stats
        """
        from models import DetectionHistory, User
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        detections = self.db.query(DetectionHistory).filter(
            DetectionHistory.timestamp >= cutoff_date
        ).all()
        
        user_stats = defaultdict(lambda: {'count': 0, 'vehicles': 0})
        
        for d in detections:
            if d.user_id:
                user_stats[d.user_id]['count'] += 1
                user_stats[d.user_id]['vehicles'] += (d.vehicle_count or 0)
        
        # Get user names
        result = []
        for user_id, stats in sorted(user_stats.items(), key=lambda x: x[1]['count'], reverse=True)[:limit]:
            user = self.db.query(User).filter(User.id == user_id).first()
            result.append({
                'user_id': user_id,
                'username': user.username if user else 'Unknown',
                'detections': stats['count'],
                'vehicles': stats['vehicles']
            })
        
        return result
    
    def get_performance_metrics(self, days=30):
        """
        Get performance metrics (processing times, confidence levels)
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dictionary with performance metrics
        """
        from models import DetectionHistory
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        detections = self.db.query(DetectionHistory).filter(
            DetectionHistory.timestamp >= cutoff_date
        ).all()
        
        processing_times = []
        confidence_levels = []
        
        for d in detections:
            if d.processing_time:
                try:
                    time_val = float(d.processing_time.replace('s', ''))
                    processing_times.append(time_val)
                except:
                    pass
            
            if d.confidence_threshold:
                confidence_levels.append(d.confidence_threshold)
        
        if not processing_times:
            return {
                'avg_processing_time': 0,
                'max_processing_time': 0,
                'min_processing_time': 0,
                'avg_confidence': 0
            }
        
        return {
            'avg_processing_time': round(sum(processing_times) / len(processing_times), 3),
            'max_processing_time': round(max(processing_times), 3),
            'min_processing_time': round(min(processing_times), 3),
            'avg_confidence': round(sum(confidence_levels) / len(confidence_levels), 3) if confidence_levels else 0
        }
