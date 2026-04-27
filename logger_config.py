"""
Logging Configuration for Vehicle Detection App
Provides structured logging with file rotation and console output
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path


def setup_logger(name: str = "vehicle_detection", log_level: str = "INFO") -> logging.Logger:
    """
    Setup and configure a logger with file and console handlers
    
    Args:
        name: Logger name
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File Handler - General logs with rotation
    general_log_file = logs_dir / f"{name}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        general_log_file,
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    # File Handler - Error logs only
    error_log_file = logs_dir / f"{name}_errors.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=5*1024*1024,  # 5 MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    logger.addHandler(error_handler)
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    return logger


def log_request(logger: logging.Logger, method: str, path: str, status_code: int, 
                response_time: float, user_id: int = None):
    """
    Log HTTP request details
    
    Args:
        logger: Logger instance
        method: HTTP method (GET, POST, etc.)
        path: Request path
        status_code: HTTP status code
        response_time: Response time in seconds
        user_id: User ID if authenticated
    """
    user_info = f"User:{user_id}" if user_id else "Anonymous"
    logger.info(f"{method} {path} | Status:{status_code} | Time:{response_time:.3f}s | {user_info}")


def log_detection(logger: logging.Logger, detection_type: str, vehicle_count: int, 
                  processing_time: float, confidence: float, user_id: int = None):
    """
    Log vehicle detection details
    
    Args:
        logger: Logger instance
        detection_type: Type of detection (image, video, live)
        vehicle_count: Number of vehicles detected
        processing_time: Processing time in seconds
        confidence: Confidence threshold used
        user_id: User ID if authenticated
    """
    user_info = f"User:{user_id}" if user_id else "Anonymous"
    logger.info(
        f"DETECTION | Type:{detection_type} | Vehicles:{vehicle_count} | "
        f"Time:{processing_time:.3f}s | Confidence:{confidence} | {user_info}"
    )


def log_error(logger: logging.Logger, error_type: str, message: str, 
              details: dict = None, user_id: int = None):
    """
    Log error details
    
    Args:
        logger: Logger instance
        error_type: Type of error (Database, Model, API, etc.)
        message: Error message
        details: Additional error details as dictionary
        user_id: User ID if authenticated
    """
    user_info = f"User:{user_id}" if user_id else "Anonymous"
    error_msg = f"ERROR | Type:{error_type} | {message} | {user_info}"
    if details:
        error_msg += f" | Details:{details}"
    logger.error(error_msg)


def log_auth_event(logger: logging.Logger, event: str, username: str, success: bool, 
                   ip_address: str = None):
    """
    Log authentication events
    
    Args:
        logger: Logger instance
        event: Event type (login, logout, register)
        username: Username
        success: Whether the operation was successful
        ip_address: IP address of the user
    """
    status = "SUCCESS" if success else "FAILED"
    ip_info = f"IP:{ip_address}" if ip_address else "IP:Unknown"
    logger.info(f"AUTH | {event.upper()} | User:{username} | {status} | {ip_info}")


def log_database_operation(logger: logging.Logger, operation: str, table: str, 
                           record_id: int = None, success: bool = True):
    """
    Log database operations
    
    Args:
        logger: Logger instance
        operation: Type of operation (INSERT, UPDATE, DELETE, SELECT)
        table: Table name
        record_id: Record ID if applicable
        success: Whether the operation was successful
    """
    status = "SUCCESS" if success else "FAILED"
    record_info = f"ID:{record_id}" if record_id else ""
    logger.debug(f"DB | {operation} | Table:{table} | {record_info} | {status}")


# Create default logger instance
default_logger = setup_logger()
