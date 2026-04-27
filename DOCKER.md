# Docker Deployment Guide

## Quick Start

### Build and Run with Docker Compose

```bash
# Build and start the container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

### Build and Run with Docker (Manual)

```bash
# Build the image
docker build -t vehicle-detection .

# Run the container
docker run -d -p 5000:5000 \
  -v $(pwd)/vehical_detections.db:/app/vehical_detections.db \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/static:/app/static \
  --name vehicle-app \
  vehicle-detection
```

## Environment Variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here
LOG_LEVEL=INFO
FLASK_ENV=production
```

## Accessing the Application

After starting the container, access the application at:
- **Web App**: http://localhost:5000
- **Health Check**: http://localhost:5000/test

## Troubleshooting

### Container won't start
```bash
# Check logs
docker logs vehicle_detection_app

# Rebuild without cache
docker-compose build --no-cache
docker-compose up -d
```

### Database issues
```bash
# Remove old database and restart
rm vehical_detections.db
docker-compose down
docker-compose up -d
```

### Port already in use
Edit `docker-compose.yml` and change the port mapping:
```yaml
ports:
  - "5001:5000"  # Use 5001 instead of 5000
```

## Production Deployment

For production deployment:
1. Change `SECRET_KEY` to a strong random value
2. Use a proper database (PostgreSQL/MySQL) instead of SQLite
3. Add SSL/TLS configuration
4. Set up proper backup strategy
5. Use environment-specific configuration files

## Volume Persistence

The following volumes are mounted for persistence:
- `vehical_detections.db` - Database file
- `logs/` - Application logs
- `static/` - Uploaded videos and images
