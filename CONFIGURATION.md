# Configuration Guide

## Environment Setup

### Step 1: Copy Environment File
```bash
cp .env.example .env
```

### Step 2: Update .env with Your Values
Edit `.env` file and set appropriate values for your environment.

## Environments

### Development (Default)
```bash
FLASK_ENV=development
SECRET_KEY=dev-secret-key
DEBUG=True
LOG_LEVEL=DEBUG
DATABASE_URL=sqlite:///vehical_detections.db
```

### Production
```bash
FLASK_ENV=production
SECRET_KEY=<strong-random-key-at-32-chars>
DEBUG=False
LOG_LEVEL=WARNING
DATABASE_URL=postgresql://user:pass@localhost/dbname
SESSION_COOKIE_SECURE=True
```

### Testing
```bash
FLASK_ENV=testing
DATABASE_URL=sqlite:///:memory:
TESTING=True
CSRF_ENABLED=False
```

### Docker
```bash
FLASK_ENV=docker
DATABASE_URL=sqlite:///vehical_detections.db
LOG_DIR=/app/logs
UPLOAD_FOLDER=/app/static
```

## Configuration Options

### Security
- `SECRET_KEY`: Flask secret key (MUST be changed in production)
- `SESSION_COOKIE_SECURE`: Enable HTTPS-only cookies (production)
- `CSRF_ENABLED`: Enable CSRF protection

### Database
- `DATABASE_URL`: Database connection string
  - SQLite: `sqlite:///path/to/db.db`
  - PostgreSQL: `postgresql://user:pass@host/db`
  - MySQL: `mysql://user:pass@host/db`

### Logging
- `LOG_LEVEL`: DEBUG, INFO, WARNING, ERROR, CRITICAL
- `LOG_DIR`: Directory for log files

### Detection
- `DEFAULT_CONFIDENCE_THRESHOLD`: Default confidence (0.0-1.0)
- `MODEL_INPUT_SIZE`: Model input size (320, 416, 480, 640)

### Performance
- `MAX_WORKERS`: Number of worker threads
- `MAX_CONTENT_LENGTH`: Max upload size in bytes

## Running with Different Environments

### Development
```bash
# .env file
FLASK_ENV=development

# Run
python web_test_app.py
```

### Production
```bash
# .env file
FLASK_ENV=production
SECRET_KEY=<strong-key>

# Run
python web_test_app.py
```

### Docker
```bash
# docker-compose.yml handles environment
docker-compose up -d
```

### Testing
```bash
# Tests automatically use testing config
pytest
```

## Security Best Practices

1. **Never commit .env file** - It's in .gitignore
2. **Use strong SECRET_KEY in production** - At least 32 random characters
3. **Use PostgreSQL/MySQL in production** - SQLite is for development only
4. **Enable HTTPS in production** - Set SESSION_COOKIE_SECURE=True
5. **Use environment variables** - Don't hardcode secrets
6. **Rotate secrets regularly** - Change SECRET_KEY periodically

## Generating Secret Key

```python
import secrets
print(secrets.token_hex(32))
```

## Troubleshooting

### Config Not Loading
```bash
# Check .env file exists
ls -la .env

# Check FLASK_ENV is set
echo $FLASK_ENV
```

### Database Connection Issues
```bash
# Check DATABASE_URL format
# SQLite: sqlite:///absolute/path/to/db.db
# PostgreSQL: postgresql://user:password@localhost:5432/dbname
```

### Import Errors
```bash
# Ensure config.py is in project root
ls config.py
```
