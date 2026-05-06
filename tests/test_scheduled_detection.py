"""
Scheduled Detection Tests for Vehicle Detection App
Tests for cron-like scheduling of detection tasks
"""
import pytest
import time
import threading


@pytest.mark.scheduled_detection
@pytest.mark.unit
def test_scheduler_initialization():
    """Test that scheduler initializes correctly"""
    from scheduled_detection import ScheduledDetectionManager
    
    scheduler = ScheduledDetectionManager()
    
    assert scheduler.is_running() is False
    assert scheduler.get_task_count() == 0


@pytest.mark.scheduled_detection
@pytest.mark.unit
def test_schedule_task():
    """Test scheduling a task"""
    from scheduled_detection import ScheduledDetectionManager
    
    scheduler = ScheduledDetectionManager()
    
    # Simple test function
    test_func = lambda: None
    
    result = scheduler.schedule_task('test_task', test_func, interval_seconds=10)
    
    assert result is True
    assert scheduler.get_task_count() == 1
    assert scheduler.is_running() is True


@pytest.mark.scheduled_detection
@pytest.mark.unit
def test_unschedule_task():
    """Test unscheduling a task"""
    from scheduled_detection import ScheduledDetectionManager
    
    scheduler = ScheduledDetectionManager()
    test_func = lambda: None
    
    scheduler.schedule_task('test_task', test_func, interval_seconds=10)
    assert scheduler.get_task_count() == 1
    
    result = scheduler.unschedule_task('test_task')
    
    assert result is True
    assert scheduler.get_task_count() == 0


@pytest.mark.scheduled_detection
@pytest.mark.unit
def test_get_task_status():
    """Test getting task status"""
    from scheduled_detection import ScheduledDetectionManager
    
    scheduler = ScheduledDetectionManager()
    test_func = lambda: None
    
    scheduler.schedule_task('test_task', test_func, interval_seconds=10)
    
    status = scheduler.get_task_status('test_task')
    
    assert status is not None
    assert status['task_id'] == 'test_task'
    assert status['interval'] == 10
    assert status['enabled'] is True


@pytest.mark.scheduled_detection
@pytest.mark.unit
def test_get_task_status_nonexistent():
    """Test getting status of non-existent task"""
    from scheduled_detection import ScheduledDetectionManager
    
    scheduler = ScheduledDetectionManager()
    
    status = scheduler.get_task_status('nonexistent')
    
    assert status is None


@pytest.mark.scheduled_detection
@pytest.mark.unit
def test_enable_disable_task():
    """Test enabling and disabling a task"""
    from scheduled_detection import ScheduledDetectionManager
    
    scheduler = ScheduledDetectionManager()
    test_func = lambda: None
    
    scheduler.schedule_task('test_task', test_func, interval_seconds=10)
    
    # Disable task
    result = scheduler.disable_task('test_task')
    assert result is True
    status = scheduler.get_task_status('test_task')
    assert status['enabled'] is False
    
    # Enable task
    result = scheduler.enable_task('test_task')
    assert result is True
    status = scheduler.get_task_status('test_task')
    assert status['enabled'] is True


@pytest.mark.scheduled_detection
@pytest.mark.unit
def test_get_all_tasks():
    """Test getting all tasks"""
    from scheduled_detection import ScheduledDetectionManager
    
    scheduler = ScheduledDetectionManager()
    test_func = lambda: None
    
    scheduler.schedule_task('task1', test_func, interval_seconds=10)
    scheduler.schedule_task('task2', test_func, interval_seconds=20)
    
    all_tasks = scheduler.get_all_tasks()
    
    assert len(all_tasks) == 2
    assert 'task1' in all_tasks
    assert 'task2' in all_tasks


@pytest.mark.scheduled_detection
@pytest.mark.unit
def test_task_execution():
    """Test that scheduled task executes"""
    from scheduled_detection import ScheduledDetectionManager
    
    scheduler = ScheduledDetectionManager()
    
    # Track execution
    execution_count = [0]
    
    def test_func():
        execution_count[0] += 1
    
    # Schedule with short interval
    scheduler.schedule_task('test_task', test_func, interval_seconds=1, start_immediately=True)
    
    # Wait for execution
    time.sleep(2)
    
    assert execution_count[0] >= 1
    
    # Cleanup
    scheduler.stop()


@pytest.mark.scheduled_detection
@pytest.mark.unit
def test_duplicate_task_id():
    """Test that duplicate task IDs are rejected"""
    from scheduled_detection import ScheduledDetectionManager
    
    scheduler = ScheduledDetectionManager()
    test_func = lambda: None
    
    scheduler.schedule_task('test_task', test_func, interval_seconds=10)
    
    # Try to schedule with same ID
    result = scheduler.schedule_task('test_task', test_func, interval_seconds=20)
    
    assert result is False
    assert scheduler.get_task_count() == 1


@pytest.mark.scheduled_detection
@pytest.mark.unit
def test_global_scheduler():
    """Test global scheduler instance"""
    from scheduled_detection import get_scheduler
    
    scheduler1 = get_scheduler()
    scheduler2 = get_scheduler()
    
    # Should return same instance
    assert scheduler1 is scheduler2


@pytest.mark.scheduled_detection
@pytest.mark.unit
def test_scheduler_stop():
    """Test stopping the scheduler"""
    from scheduled_detection import ScheduledDetectionManager
    
    scheduler = ScheduledDetectionManager()
    test_func = lambda: None
    
    scheduler.schedule_task('test_task', test_func, interval_seconds=10)
    assert scheduler.is_running() is True
    
    scheduler.stop()
    assert scheduler.is_running() is False
