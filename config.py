"""
Configuration management for Vehicle Detection App
Supports different environments: development, production, testing
"""
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration"""
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = False
    TESTING = False
    
    # Database settings
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///vehical_detections.db')
    
    # Logging settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_DIR = os.getenv('LOG_DIR', 'logs')
    
    # Upload settings
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100 MB max upload
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'static')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'mp4', 'avi', 'mov'}
    
    # Detection settings
    DEFAULT_CONFIDENCE_THRESHOLD = float(os.getenv('DEFAULT_CONFIDENCE_THRESHOLD', '0.35'))
    MODEL_INPUT_SIZE = int(os.getenv('MODEL_INPUT_SIZE', '640'))
    ENABLE_IMAGE_ENHANCEMENT = os.getenv('ENABLE_IMAGE_ENHANCEMENT', 'True').lower() == 'true'
    
    # Session settings
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    
    # Performance settings
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', '4'))
    
    # Security settings
    CSRF_ENABLED = True
    WTF_CSRF_ENABLED = True
    
    # Error Monitoring (Sentry)
    SENTRY_DSN = os.getenv('SENTRY_DSN', '')
    SENTRY_ENVIRONMENT = os.getenv('FLASK_ENV', 'development')
    SENTRY_SAMPLE_RATE = float(os.getenv('SENTRY_SAMPLE_RATE', '1.0'))
    
    # Caching (Redis)
    CACHE_TYPE = os.getenv('CACHE_TYPE', 'simple')  # 'simple', 'redis', 'memcached'
    CACHE_REDIS_URL = os.getenv('CACHE_REDIS_URL', 'redis://localhost:6379/0')
    CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_DEFAULT_TIMEOUT', '300'))  # 5 minutes
    
    # Language Settings
    DEFAULT_LANGUAGE = os.getenv('DEFAULT_LANGUAGE', 'en')  # 'en' or 'hi'
    SUPPORTED_LANGUAGES = ['en', 'hi']
    
    # Email Settings
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@vehicledetection.com')
    MAIL_ENABLED = os.getenv('MAIL_ENABLED', 'False').lower() == 'true'
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration"""
        # Create necessary directories
        Path(Config.LOG_DIR).mkdir(exist_ok=True)
        Path(Config.UPLOAD_FOLDER).mkdir(exist_ok=True)
        Path(f"{Config.UPLOAD_FOLDER}/videos").mkdir(exist_ok=True)
        Path(f"{Config.UPLOAD_FOLDER}/demo_videos").mkdir(exist_ok=True)


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    
    # Development database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///vehical_detections.db')
    
    # Less secure for development
    SESSION_COOKIE_SECURE = False
    CSRF_ENABLED = True
    
    # Verbose logging in development
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Production should use PostgreSQL or MySQL
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///vehical_detections.db')
    
    # Secure cookies in production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    
    # CSRF protection
    CSRF_ENABLED = True
    
    # Production logging
    LOG_LEVEL = 'WARNING'
    
    # Production secret key must be set
    if os.getenv('SECRET_KEY') == 'dev-secret-key-change-in-production':
        raise ValueError("SECRET_KEY must be set in production!")


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    
    # In-memory database for testing
    DATABASE_URL = 'sqlite:///:memory:'
    
    # Disable CSRF for testing
    CSRF_ENABLED = False
    WTF_CSRF_ENABLED = False
    
    # Testing logging
    LOG_LEVEL = 'DEBUG'
    
    # Faster session expiry for testing
    PERMANENT_SESSION_LIFETIME = 60  # 1 minute


class DockerConfig(Config):
    """Docker deployment configuration"""
    DEBUG = False
    TESTING = False
    
    # Docker-specific settings
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///vehical_detections.db')
    LOG_DIR = '/app/logs'
    UPLOAD_FOLDER = '/app/static'
    
    # Secure settings
    SESSION_COOKIE_SECURE = False  # May be behind reverse proxy
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'docker': DockerConfig,
    'default': DevelopmentConfig
}


def get_config(env=None):
    """
    Get configuration based on environment
    
    Args:
        env: Environment name (development, production, testing, docker)
              If None, reads from FLASK_ENV or defaults to development
    
    Returns:
        Configuration class
    """
    if env is None:
        env = os.getenv('FLASK_ENV', os.getenv('ENV', 'development'))
    
    return config.get(env.lower(), config['default'])
