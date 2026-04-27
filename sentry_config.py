"""
Sentry Error Monitoring Configuration
"""
import os
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.logging import LoggingIntegration


def init_sentry(dsn=None, environment=None, sample_rate=1.0):
    """
    Initialize Sentry for error monitoring
    
    Args:
        dsn: Sentry DSN (Data Source Name)
        environment: Environment name (development, production, etc.)
        sample_rate: Error sampling rate (0.0 to 1.0)
    
    Returns:
        True if Sentry initialized, False otherwise
    """
    # Get DSN from environment if not provided
    if dsn is None:
        dsn = os.getenv('SENTRY_DSN')
    
    # Get environment from environment variable if not provided
    if environment is None:
        environment = os.getenv('FLASK_ENV', os.getenv('ENV', 'development'))
    
    # Don't initialize in testing or if no DSN provided
    if not dsn or environment == 'testing':
        return False
    
    try:
        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            sample_rate=sample_rate,
            integrations=[
                FlaskIntegration(),
                SqlalchemyIntegration(),
                LoggingIntegration(
                    level=logging.INFO,  # Capture info and above as breadcrumbs
                    event_level=logging.ERROR  # Send errors as events
                )
            ],
            traces_sample_rate=0.1,  # Capture 10% of transactions for performance monitoring
            profiles_sample_rate=0.1,  # Capture 10% of profiles
            send_default_pii=False,  # Don't send personally identifiable information
            before_send=before_send_filter,  # Filter errors before sending
            ignore_errors=[
                # Ignore common expected errors
                KeyboardInterrupt,
                SystemExit,
            ]
        )
        return True
    except Exception as e:
        print(f"[WARNING] Failed to initialize Sentry: {e}")
        return False


def before_send(event, hint):
    """
    Filter and modify events before sending to Sentry
    
    Args:
        event: Sentry event dictionary
        hint: Hint dictionary with original exception
    
    Returns:
        Modified event or None to skip sending
    """
    # Filter out sensitive data
    if 'request' in event and 'data' in event['request']:
        # Remove passwords from form data
        if 'password' in event['request']['data']:
            event['request']['data']['password'] = '[FILTERED]'
        if 'confirm_password' in event['request']['data']:
            event['request']['data']['confirm_password'] = '[FILTERED]'
    
    # Add custom tags
    if 'tags' not in event:
        event['tags'] = {}
    event['tags']['app'] = 'vehicle-detection'
    event['tags']['environment'] = os.getenv('FLASK_ENV', 'development')
    
    # Add user context if available
    try:
        from flask import session
        if 'user_id' in session:
            sentry_sdk.set_user({
                'id': str(session['user_id']),
                'username': session.get('username', 'unknown')
            })
    except:
        pass
    
    return event


def capture_exception(exception, extra=None):
    """
    Capture an exception and send to Sentry
    
    Args:
        exception: Exception object
        extra: Additional context data
    """
    with sentry_sdk.push_scope() as scope:
        if extra:
            for key, value in extra.items():
                scope.set_extra(key, value)
        sentry_sdk.capture_exception(exception)


def capture_message(message, level='info'):
    """
    Capture a message and send to Sentry
    
    Args:
        message: Message string
        level: Log level (info, warning, error)
    """
    sentry_sdk.capture_message(message, level=level)


def set_user_context(user_id, username=None, email=None):
    """
    Set user context for Sentry events
    
    Args:
        user_id: User ID
        username: Username
        email: Email address
    """
    user_data = {'id': str(user_id)}
    if username:
        user_data['username'] = username
    if email:
        user_data['email'] = email
    
    sentry_sdk.set_user(user_data)


def add_breadcrumb(category, message, level='info', data=None):
    """
    Add a breadcrumb for context
    
    Args:
        category: Breadcrumb category
        message: Breadcrumb message
        level: Log level
        data: Additional data
    """
    sentry_sdk.add_breadcrumb(
        category=category,
        message=message,
        level=level,
        data=data
    )
