"""
Backup and Restore Service for Vehicle Detection App
Handles database backup and restore operations
"""
import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
import zipfile
import json


class BackupService:
    """Service for database backup and restore"""
    
    def __init__(self, db_path=None, backup_dir=None):
        """
        Initialize backup service
        
        Args:
            db_path: Path to database file
            backup_dir: Directory for backups
        """
        self.db_path = db_path or os.getenv('DATABASE_PATH', 'vehical_detections.db')
        self.backup_dir = backup_dir or os.getenv('BACKUP_DIR', 'backups')
        
        # Create backup directory if it doesn't exist
        Path(self.backup_dir).mkdir(exist_ok=True)
    
    def create_backup(self, include_static=False):
        """
        Create a database backup
        
        Args:
            include_static: Whether to include static files (videos, images)
        
        Returns:
            Tuple of (success, message, backup_path)
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"backup_{timestamp}.zip"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Check if database exists
            if not os.path.exists(self.db_path):
                return False, "Database file not found", None
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add database file
                zipf.write(self.db_path, os.path.basename(self.db_path))
                
                # Add metadata
                metadata = {
                    'timestamp': timestamp,
                    'database_path': self.db_path,
                    'backup_type': 'full' if include_static else 'database_only',
                    'created_at': datetime.now().isoformat()
                }
                zipf.writestr('metadata.json', json.dumps(metadata, indent=2))
                
                # Add static files if requested
                if include_static:
                    static_dir = 'static'
                    if os.path.exists(static_dir):
                        for root, dirs, files in os.walk(static_dir):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path)
                                zipf.write(file_path, arcname)
            
            return True, f"Backup created: {backup_filename}", backup_path
            
        except Exception as e:
            return False, f"Backup failed: {str(e)}", None
    
    def restore_backup(self, backup_path):
        """
        Restore database from backup
        
        Args:
            backup_path: Path to backup file
        
        Returns:
            Tuple of (success, message)
        """
        try:
            if not os.path.exists(backup_path):
                return False, "Backup file not found"
            
            # Create a backup of current database before restore
            current_backup = f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            if os.path.exists(self.db_path):
                shutil.copy2(self.db_path, os.path.join(self.backup_dir, current_backup))
            
            # Extract backup
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # Read metadata
                if 'metadata.json' in zipf.namelist():
                    metadata = json.loads(zipf.read('metadata.json').decode('utf-8'))
                else:
                    metadata = {}
                
                # Extract database
                db_file = None
                for file in zipf.namelist():
                    if file.endswith('.db'):
                        db_file = file
                        break
                
                if not db_file:
                    return False, "No database file found in backup"
                
                # Extract database to temp location first
                temp_db = f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                zipf.extract(db_file, temp_db)
                
                # Replace current database
                extracted_db = os.path.join(temp_db, db_file)
                shutil.move(extracted_db, self.db_path)
                
                # Clean up temp directory
                os.rmdir(temp_db)
                
                # Extract static files if included
                if metadata.get('backup_type') == 'full':
                    for file in zipf.namelist():
                        if file.startswith('static/') and not file.endswith('/'):
                            zipf.extract(file)
            
            return True, f"Database restored from backup (created: {metadata.get('timestamp', 'unknown')})"
            
        except Exception as e:
            return False, f"Restore failed: {str(e)}"
    
    def list_backups(self):
        """
        List all available backups
        
        Returns:
            List of backup information dictionaries
        """
        backups = []
        
        if not os.path.exists(self.backup_dir):
            return backups
        
        for file in os.listdir(self.backup_dir):
            if file.endswith('.zip'):
                file_path = os.path.join(self.backup_dir, file)
                file_stat = os.stat(file_path)
                
                # Try to read metadata
                metadata = {}
                try:
                    with zipfile.ZipFile(file_path, 'r') as zipf:
                        if 'metadata.json' in zipf.namelist():
                            metadata = json.loads(zipf.read('metadata.json').decode('utf-8'))
                except:
                    pass
                
                backups.append({
                    'filename': file,
                    'path': file_path,
                    'size': file_stat.st_size,
                    'created': datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'type': metadata.get('backup_type', 'unknown'),
                    'timestamp': metadata.get('timestamp', 'unknown')
                })
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x['created'], reverse=True)
        
        return backups
    
    def delete_backup(self, backup_path):
        """
        Delete a backup file
        
        Args:
            backup_path: Path to backup file
        
        Returns:
            Tuple of (success, message)
        """
        try:
            if not os.path.exists(backup_path):
                return False, "Backup file not found"
            
            os.remove(backup_path)
            return True, "Backup deleted successfully"
            
        except Exception as e:
            return False, f"Delete failed: {str(e)}"
    
    def cleanup_old_backups(self, keep_days=30):
        """
        Delete backups older than specified days
        
        Args:
            keep_days: Number of days to keep backups
        
        Returns:
            Tuple of (deleted_count, message)
        """
        try:
            if not os.path.exists(self.backup_dir):
                return 0, "Backup directory not found"
            
            cutoff_time = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
            deleted_count = 0
            
            for file in os.listdir(self.backup_dir):
                if file.endswith('.zip'):
                    file_path = os.path.join(self.backup_dir, file)
                    file_stat = os.stat(file_path)
                    
                    if file_stat.st_mtime < cutoff_time:
                        os.remove(file_path)
                        deleted_count += 1
            
            return deleted_count, f"Deleted {deleted_count} old backups"
            
        except Exception as e:
            return 0, f"Cleanup failed: {str(e)}"
    
    def get_database_info(self):
        """
        Get database information
        
        Returns:
            Dictionary with database info
        """
        try:
            if not os.path.exists(self.db_path):
                return {'exists': False}
            
            file_stat = os.stat(self.db_path)
            
            # Get database size in MB
            size_mb = file_stat.st_size / (1024 * 1024)
            
            # Get table counts
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            tables = {}
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            for table in cursor.fetchall():
                table_name = table[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                tables[table_name] = count
            
            conn.close()
            
            return {
                'exists': True,
                'path': self.db_path,
                'size_mb': round(size_mb, 2),
                'modified': datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'tables': tables
            }
            
        except Exception as e:
            return {'exists': False, 'error': str(e)}
