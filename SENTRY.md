# Sentry Error Monitoring Guide

## Overview

Sentry provides real-time error tracking and performance monitoring for your Vehicle Detection application. It automatically captures exceptions and provides detailed debugging information.

## Setup

### Step 1: Create Sentry Account

1. Go to https://sentry.io/
2. Sign up for a free account
3. Create a new project
4. Select "Python" as the platform
5. Copy your DSN (Data Source Name)

### Step 2: Configure Sentry

Add your Sentry DSN to the `.env` file:

```bash
SENTRY_DSN=https://your-dsn@sentry.io/project-id
```

### Step 3: Install Dependencies

```bash
pip install sentry-sdk
```

Or if using requirements.txt:
```bash
pip install -r requirements.txt
```

### Step 4: Restart Application

```bash
python web_test_app.py
```

Sentry will automatically initialize if `SENTRY_DSN` is set.

## Features

### Automatic Error Capture

Sentry automatically captures:
- Unhandled exceptions
- HTTP errors
- Database errors
- Request/response data (filtered for sensitive info)

### Performance Monitoring

Sentry tracks:
- Request response times
- Database query performance
- Transaction traces

### User Context

Sentry automatically captures:
- User ID (if logged in)
- Username
- Request headers
- IP address

### Breadcrumbs

Sentry tracks user actions leading up to errors:
- Navigation
- API calls
- Database queries

## Manual Error Reporting

### Capture Exception

```python
import sentry_config

try:
    # Your code that might fail
    result = risky_operation()
except Exception as e:
    sentry_config.capture_exception(e, extra={
        'context': 'additional context',
        'user_input': user_data
    })
```

### Capture Message

```python
import sentry_config

sentry_config.capture_message("Custom message", level='warning')
```

### Set User Context

```python
import sentry_config

sentry_config.set_user_context(
    user_id=123,
    username='john_doe',
    email='john@example.com'
)
```

### Add Breadcrumb

```python
import sentry_config

sentry_config.add_breadcrumb(
    category='user_action',
    message='User clicked detect button',
    level='info',
    data={'image_id': 'img_123'}
)
```

## Configuration Options

### Environment Variables

```bash
# Sentry DSN (required for Sentry to work)
SENTRY_DSN=https://your-dsn@sentry.io/project-id

# Environment name (development, production, staging)
FLASK_ENV=production

# Error sampling rate (0.0 to 1.0)
SENTRY_SAMPLE_RATE=1.0
```

### Sampling Rates

- **Error Sample Rate**: Fraction of errors to send (1.0 = all errors)
- **Transaction Sample Rate**: Fraction of transactions to track (default 0.1)
- **Profile Sample Rate**: Fraction of profiles to capture (default 0.1)

## Security

### Data Filtering

Sentry automatically filters:
- Passwords from form data
- Sensitive headers
- Personally identifiable information (PII)

### PII Control

```python
# In config.py
SENTRY_SEND_DEFAULT_PII=False  # Don't send PII
```

## Testing Sentry

### Trigger Test Error

Add this temporary route to test Sentry:

```python
@app.route('/sentry-test')
def sentry_test():
    1 / 0  # This will trigger an error
```

Visit `/sentry-test` to verify Sentry is working.

## Production Deployment

### Enable in Production

```bash
# .env for production
FLASK_ENV=production
SENTRY_DSN=https://your-production-dsn@sentry.io/project-id
SENTRY_SAMPLE_RATE=1.0
```

### Disable in Development

```bash
# .env for development
FLASK_ENV=development
SENTRY_DSN=  # Leave empty to disable
```

### Disable in Testing

Sentry is automatically disabled in testing mode.

## Monitoring Dashboard

Access your Sentry dashboard at:
```
https://sentry.io/organizations/your-org/projects/your-project/
```

### Key Metrics to Monitor

1. **Error Rate**: Number of errors per request
2. **Response Time**: Average response time
3. **Crash Free Users**: Percentage of users without errors
4. **Top Errors**: Most frequent errors

## Alerts

Set up alerts in Sentry to notify you:

1. Go to Settings → Alerts
2. Create new alert rule
3. Configure conditions (error rate, error count, etc.)
4. Set notification channels (email, Slack, etc.)

## Troubleshooting

### Sentry Not Receiving Errors

1. Check `SENTRY_DSN` is set correctly
2. Check network connectivity to Sentry
3. Check logs for Sentry initialization message
4. Verify environment is not 'testing'

### Too Many Errors

Reduce sampling rate:
```bash
SENTRY_SAMPLE_RATE=0.1  # Send only 10% of errors
```

### Sensitive Data Leaking

1. Check `before_send` filter in `sentry_config.py`
2. Review Sentry data scrubbing settings
3. Ensure `SENTRY_SEND_DEFAULT_PII=False`

## Integration with Logging

Sentry integrates with your logging system:
- INFO logs become breadcrumbs
- WARNING and ERROR logs are sent as events
- Log context is included in error reports

## Cost Management

### Free Tier Limits

- Sentry free tier: 5,000 errors/month
- Optimize by:
  - Using sampling rates
  - Filtering expected errors
  - Setting environment-specific rates

### Upgrade Considerations

Upgrade to paid plan if:
- High traffic application
- Need extended retention
- Need advanced features
- Require team collaboration

## Best Practices

1. **Always set environment name** (development, production)
2. **Use appropriate sampling rates** for production
3. **Review error trends** regularly
4. **Set up alerts** for critical errors
5. **Filter expected errors** to reduce noise
6. **Add user context** for better debugging
7. **Use breadcrumbs** to track user flow
8. **Keep DSN secure** - never commit to git
9. **Test in staging** before production
10. **Monitor costs** with sampling rates

## Disabling Sentry

To temporarily disable Sentry without removing code:

```bash
# In .env
SENTRY_DSN=
```

Or set environment to testing:

```bash
FLASK_ENV=testing
```
