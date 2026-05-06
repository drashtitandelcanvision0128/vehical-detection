"""
Scheduled Detection Manager for Vehicle Detection App
Cron-like scheduling for automated detection tasks with database persistence
"""
import threading
import time
from datetime import datetime, timedelta
from typing import Callable, Optional, Dict, Any
import logging


class ScheduledDetectionManager:
    """
    Manager for scheduled/automated detection tasks
    Supports interval-based scheduling and database persistence
    """
    
    def __init__(self):
        """Initialize the scheduled detection manager"""
        from logger_config import setup_logger
        self.scheduled_tasks = {}  # {task_id: {'func': ..., 'interval': ..., 'last_run': ..., 'source': ..., 'type': ...}}
        self.running = False
        self.scheduler_thread = None
        self.logger = setup_logger("scheduled_detection")
        self.db_session_factory = None
        self.task_factory = None  # Function to recreate task_func from metadata
        print("[INFO] ScheduledDetectionManager initialized.")
    
    def configure(self, db_session_factory: Callable, task_factory: Callable):
        """
        Configure the manager with database and task creation logic
        
        Args:
            db_session_factory: Callable that returns a SQLAlchemy session
            task_factory: Callable that takes (task_id, source, task_type) and returns a task function
        """
        self.db_session_factory = db_session_factory
        self.task_factory = task_factory
        self.logger.info("Scheduler configured with DB persistence and task factory")
        
        # Load existing tasks from database
        self.load_tasks_from_db()
    
    def load_tasks_from_db(self):
        """Load scheduled tasks from the database"""
        if not self.db_session_factory or not self.task_factory:
            self.logger.warning("Cannot load tasks: Scheduler not fully configured")
            return
            
        try:
            from models import ScheduledTask
            session = self.db_session_factory()
            tasks = session.query(ScheduledTask).all()
            
            count = 0
            for task in tasks:
                if task.task_id not in self.scheduled_tasks:
                    # Recreate the task function
                    task_func = self.task_factory(task.task_id, task.source, task.task_type)
                    
                    self.scheduled_tasks[task.task_id] = {
                        'func': task_func,
                        'interval': task.interval_seconds,
                        'last_run': task.last_run,
                        'next_run': task.next_run or (datetime.now() + timedelta(seconds=task.interval_seconds)),
                        'enabled': bool(task.enabled),
                        'source': task.source,
                        'type': task.task_type
                    }
                    count += 1
            
            session.close()
            self.logger.info(f"Loaded {count} tasks from database")
            
            if count > 0 and not self.running:
                self.start()
                
        except Exception as e:
            self.logger.error(f"Error loading tasks from DB: {e}")
    
    def schedule_task(self, task_id: str, task_func: Callable, interval_seconds: int, 
                     source: str = "0", task_type: str = "webcam",
                     start_immediately: bool = False, persist: bool = True) -> bool:
        """
        Schedule a detection task to run at regular intervals
        
        Args:
            task_id: Unique identifier for the task
            task_func: Function to call (should accept no arguments)
            interval_seconds: Interval in seconds between runs
            source: Input source (e.g., camera index or file path)
            task_type: Type of task (e.g., 'webcam', 'file')
            start_immediately: If True, run immediately on start
            persist: If True, save to database
            
        Returns:
            True if scheduled successfully, False otherwise
        """
        if task_id in self.scheduled_tasks:
            self.logger.warning(f"Task {task_id} already exists")
            return False
        
        now = datetime.now()
        next_run = now if start_immediately else now + timedelta(seconds=interval_seconds)
        
        self.scheduled_tasks[task_id] = {
            'func': task_func,
            'interval': interval_seconds,
            'last_run': None,
            'next_run': next_run,
            'enabled': True,
            'source': source,
            'type': task_type
        }
        
        # Persist to database if configured
        if persist:
            if not self.db_session_factory:
                self.logger.warning(f"Task {task_id} NOT persisted: db_session_factory is None")
            else:
                try:
                    from models import ScheduledTask
                    session = self.db_session_factory()
                    if not session:
                        self.logger.error(f"Task {task_id} NOT persisted: session creation failed")
                    else:
                        # Check if already exists in DB
                        db_task = session.query(ScheduledTask).filter_by(task_id=task_id).first()
                        if not db_task:
                            db_task = ScheduledTask(
                                task_id=task_id,
                                interval_seconds=interval_seconds,
                                source=source,
                                task_type=task_type,
                                enabled=1,
                                next_run=next_run
                            )
                            session.add(db_task)
                        else:
                            db_task.interval_seconds = interval_seconds
                            db_task.source = source
                            db_task.task_type = task_type
                            db_task.enabled = 1
                            db_task.next_run = next_run
                        
                        session.commit()
                        session.close()
                        self.logger.info(f"Task {task_id} persisted to database successfully")
                except Exception as e:
                    self.logger.error(f"Error persisting task {task_id} to DB: {e}")
                    import traceback
                    self.logger.error(traceback.format_exc())
        
        self.logger.info(f"Task {task_id} scheduled with interval {interval_seconds}s")
        
        # Start scheduler if not running
        if not self.running:
            self.start()
        
        return True
    
    def unschedule_task(self, task_id: str) -> bool:
        """
        Remove a scheduled task
        
        Args:
            task_id: Task identifier
            
        Returns:
            True if removed successfully, False otherwise
        """
        if task_id not in self.scheduled_tasks:
            self.logger.warning(f"Task {task_id} not found")
            return False
        
        del self.scheduled_tasks[task_id]
        
        # Remove from database if configured
        if self.db_session_factory:
            try:
                from models import ScheduledTask
                session = self.db_session_factory()
                db_task = session.query(ScheduledTask).filter_by(task_id=task_id).first()
                if db_task:
                    session.delete(db_task)
                    session.commit()
                    self.logger.info(f"Task {task_id} removed from database")
                session.close()
            except Exception as e:
                self.logger.error(f"Error removing task from DB: {e}")
                
        self.logger.info(f"Task {task_id} unscheduled")
        
        # Stop scheduler if no tasks remain
        if not self.scheduled_tasks:
            self.stop()
        
        return True
    
    def enable_task(self, task_id: str) -> bool:
        """Enable a scheduled task"""
        if task_id in self.scheduled_tasks:
            self.scheduled_tasks[task_id]['enabled'] = True
            
            # Update DB
            if self.db_session_factory:
                try:
                    from models import ScheduledTask
                    session = self.db_session_factory()
                    db_task = session.query(ScheduledTask).filter_by(task_id=task_id).first()
                    if db_task:
                        db_task.enabled = 1
                        session.commit()
                    session.close()
                except Exception as e:
                    self.logger.error(f"Error enabling task in DB: {e}")
                    
            self.logger.info(f"Task {task_id} enabled")
            return True
        return False
    
    def disable_task(self, task_id: str) -> bool:
        """Disable a scheduled task"""
        if task_id in self.scheduled_tasks:
            self.scheduled_tasks[task_id]['enabled'] = False
            
            # Update DB
            if self.db_session_factory:
                try:
                    from models import ScheduledTask
                    session = self.db_session_factory()
                    db_task = session.query(ScheduledTask).filter_by(task_id=task_id).first()
                    if db_task:
                        db_task.enabled = 0
                        session.commit()
                    session.close()
                except Exception as e:
                    self.logger.error(f"Error disabling task in DB: {e}")
                    
            self.logger.info(f"Task {task_id} disabled")
            return True
        return False
    
    def get_task_status(self, task_id: str) -> Optional[dict]:
        """Get status of a scheduled task"""
        if task_id not in self.scheduled_tasks:
            return None
        
        task = self.scheduled_tasks[task_id]
        return {
            'task_id': task_id,
            'interval': task['interval'],
            'enabled': task['enabled'],
            'source': task.get('source', '0'),
            'type': task.get('type', 'webcam'),
            'last_run': task['last_run'].isoformat() if task['last_run'] else None,
            'next_run': task['next_run'].isoformat() if task['next_run'] else None
        }
    
    def get_all_tasks(self) -> dict:
        """Get status of all scheduled tasks"""
        return {tid: self.get_task_status(tid) for tid in self.scheduled_tasks}
    
    def start(self):
        """Start the scheduler"""
        if self.running:
            self.logger.warning("Scheduler already running")
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        self.logger.info("Scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        if not self.running:
            return
        
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=2.0)
        self.logger.info("Scheduler stopped")
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        self.logger.info("Scheduler loop started")
        while self.running:
            now = datetime.now()
            
            for task_id, task in list(self.scheduled_tasks.items()):
                if not task['enabled']:
                    continue
                
                if now >= task['next_run']:
                    msg = f"[{datetime.now().strftime('%H:%M:%S')}] >>> TRIGGERING TASK: {task_id}"
                    print(msg)
                    self.logger.info(msg)
                    try:
                        # Update timing before run to avoid double trigger if task is slow
                        last_run = now
                        next_run = now + timedelta(seconds=task['interval'])
                        
                        task['func']()
                        
                        task['last_run'] = last_run
                        task['next_run'] = next_run
                        
                        # Update DB
                        if self.db_session_factory:
                            try:
                                from models import ScheduledTask
                                session = self.db_session_factory()
                                db_task = session.query(ScheduledTask).filter_by(task_id=task_id).first()
                                if db_task:
                                    db_task.last_run = last_run
                                    db_task.next_run = next_run
                                    session.commit()
                                session.close()
                            except Exception as db_e:
                                self.logger.error(f"Error updating task timing in DB: {db_e}")
                                
                        msg = f"[{datetime.now().strftime('%H:%M:%S')}] <<< TASK {task_id} COMPLETED SUCCESSFULLY"
                        print(msg)
                        self.logger.info(msg)
                    except Exception as e:
                        self.logger.error(f"Task {task_id} failed: {e}")
                        import traceback
                        self.logger.error(traceback.format_exc())
                        # Still update next run time to prevent infinite loop of failures
                        task['next_run'] = now + timedelta(seconds=task['interval'])
            
            time.sleep(1)
        self.logger.info("Scheduler loop stopped")
    
    def is_running(self) -> bool:
        """Check if scheduler is running"""
        return self.running
    
    def get_task_count(self) -> int:
        """Get number of scheduled tasks"""
        return len(self.scheduled_tasks)


# Global scheduler instance
_scheduler_instance = None


def get_scheduler() -> ScheduledDetectionManager:
    """Get or create the global scheduler instance"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = ScheduledDetectionManager()
    return _scheduler_instance
