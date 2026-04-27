"""
Data Export Service for Vehicle Detection App
Provides CSV and Excel export functionality
"""
import pandas as pd
from datetime import datetime
from io import BytesIO


class ExportService:
    """Service for exporting detection data"""
    
    def __init__(self, db_session):
        """
        Initialize export service
        
        Args:
            db_session: Database session
        """
        self.db = db_session
    
    def export_history_to_csv(self, days=30):
        """
        Export detection history to CSV
        
        Args:
            days: Number of days to export
        
        Returns:
            Tuple of (filename, csv_bytes)
        """
        from models import DetectionHistory
        
        cutoff_date = datetime.utcnow() - pd.Timedelta(days=days)
        
        detections = self.db.query(DetectionHistory).filter(
            DetectionHistory.timestamp >= cutoff_date
        ).all()
        
        # Convert to list of dictionaries
        data = []
        for d in detections:
            data.append({
                'Report ID': d.report_id,
                'Type': d.detection_type,
                'Timestamp': d.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'Vehicle Count': d.vehicle_count or 0,
                'Processing Time': d.processing_time or '',
                'Confidence Threshold': d.confidence_threshold or 0,
                'Breakdown': d.breakdown or ''
            })
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Generate filename
        filename = f"vehicle_detection_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Convert to CSV bytes
        csv_bytes = df.to_csv(index=False).encode('utf-8')
        
        return filename, csv_bytes
    
    def export_history_to_excel(self, days=30):
        """
        Export detection history to Excel
        
        Args:
            days: Number of days to export
        
        Returns:
            Tuple of (filename, excel_bytes)
        """
        from models import DetectionHistory
        
        cutoff_date = datetime.utcnow() - pd.Timedelta(days=days)
        
        detections = self.db.query(DetectionHistory).filter(
            DetectionHistory.timestamp >= cutoff_date
        ).all()
        
        # Convert to list of dictionaries
        data = []
        for d in detections:
            data.append({
                'Report ID': d.report_id,
                'Type': d.detection_type,
                'Timestamp': d.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'Vehicle Count': d.vehicle_count or 0,
                'Processing Time': d.processing_time or '',
                'Confidence Threshold': d.confidence_threshold or 0,
                'Breakdown': d.breakdown or ''
            })
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Generate filename
        filename = f"vehicle_detection_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        # Convert to Excel bytes
        excel_bytes = BytesIO()
        with pd.ExcelWriter(excel_bytes, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Detection History')
        
        excel_bytes.seek(0)
        
        return filename, excel_bytes.getvalue()
    
    def export_analytics_to_csv(self, days=30):
        """
        Export analytics summary to CSV
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Tuple of (filename, csv_bytes)
        """
        from analytics_service import AnalyticsService
        
        analytics = AnalyticsService(self.db)
        
        # Get all analytics data
        overall_stats = analytics.get_overall_stats(days=days)
        detection_by_type = analytics.get_detection_by_type(days=days)
        vehicle_breakdown = analytics.get_vehicle_breakdown(days=days)
        
        # Create summary data
        data = [
            ['Overall Statistics', '', ''],
            ['Total Detections', overall_stats['total_detections'], ''],
            ['Total Vehicles', overall_stats['total_vehicles'], ''],
            ['Avg Vehicles per Detection', overall_stats['avg_vehicles_per_detection'], ''],
            ['Avg Processing Time', overall_stats['avg_processing_time'], ''],
            ['', '', ''],
            ['Detection by Type', '', ''],
            ['Image', detection_by_type['image'], ''],
            ['Video', detection_by_type['video'], ''],
            ['Live', detection_by_type['live'], ''],
            ['', '', ''],
            ['Vehicle Breakdown', '', ''],
        ]
        
        for vehicle, count in vehicle_breakdown.items():
            data.append([vehicle, count, ''])
        
        # Create DataFrame
        df = pd.DataFrame(data, columns=['Metric', 'Value', 'Notes'])
        
        # Generate filename
        filename = f"vehicle_detection_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Convert to CSV bytes
        csv_bytes = df.to_csv(index=False).encode('utf-8')
        
        return filename, csv_bytes
    
    def export_analytics_to_excel(self, days=30):
        """
        Export analytics summary to Excel with multiple sheets
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Tuple of (filename, excel_bytes)
        """
        from analytics_service import AnalyticsService
        
        analytics = AnalyticsService(self.db)
        
        # Get all analytics data
        overall_stats = analytics.get_overall_stats(days=days)
        detection_by_type = analytics.get_detection_by_type(days=days)
        vehicle_breakdown = analytics.get_vehicle_breakdown(days=days)
        daily_trends = analytics.get_daily_trends(days=days)
        user_activity = analytics.get_user_activity(days=days, limit=50)
        
        # Generate filename
        filename = f"vehicle_detection_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        # Convert to Excel bytes
        excel_bytes = BytesIO()
        with pd.ExcelWriter(excel_bytes, engine='openpyxl') as writer:
            # Sheet 1: Overall Statistics
            overall_data = {
                'Metric': ['Total Detections', 'Total Vehicles', 'Avg Vehicles per Detection', 
                          'Avg Processing Time', 'Most Common Vehicle'],
                'Value': [overall_stats['total_detections'], overall_stats['total_vehicles'],
                         overall_stats['avg_vehicles_per_detection'], overall_stats['avg_processing_time'],
                         overall_stats['most_common_vehicle']]
            }
            pd.DataFrame(overall_data).to_excel(writer, index=False, sheet_name='Overview')
            
            # Sheet 2: Detection by Type
            type_data = {
                'Type': ['Image', 'Video', 'Live'],
                'Count': [detection_by_type['image'], detection_by_type['video'], detection_by_type['live']]
            }
            pd.DataFrame(type_data).to_excel(writer, index=False, sheet_name='By Type')
            
            # Sheet 3: Vehicle Breakdown
            vehicle_df = pd.DataFrame(list(vehicle_breakdown.items()), columns=['Vehicle Type', 'Count'])
            vehicle_df.to_excel(writer, index=False, sheet_name='Vehicle Breakdown')
            
            # Sheet 4: Daily Trends
            trend_df = pd.DataFrame(daily_trends)
            trend_df.to_excel(writer, index=False, sheet_name='Daily Trends')
            
            # Sheet 5: User Activity
            user_df = pd.DataFrame(user_activity)
            user_df.to_excel(writer, index=False, sheet_name='User Activity')
        
        excel_bytes.seek(0)
        
        return filename, excel_bytes.getvalue()
