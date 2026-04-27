# API Documentation Guide

## Accessing API Documentation

Once the application is running, access the Swagger UI at:
```
http://localhost:5000/api/docs
```

## API Endpoints

### Authentication Endpoints

#### POST /login
User login endpoint

**Request:**
- Content-Type: application/x-www-form-urlencoded
- Body:
  - username (string, required)
  - password (string, required)

**Response:**
- 200: Login successful
- 401: Invalid credentials

#### POST /register
User registration endpoint

**Request:**
- Content-Type: application/x-www-form-urlencoded
- Body:
  - username (string, required, unique)
  - email (string, required, unique)
  - password (string, required, min 6 chars)
  - confirm_password (string, required)

**Response:**
- 200: Registration successful
- 400: Invalid input or user already exists

#### GET /logout
User logout endpoint

**Response:**
- 200: Logout successful

### Detection Endpoints

#### GET /history
Get detection history (requires authentication)

**Security:** Bearer token required

**Response:**
- 200: Detection history retrieved
- 401: Not authenticated

#### POST /webcam_detect
Process webcam frame for vehicle detection

**Request:**
- Content-Type: multipart/form-data
- Body: image data

**Response:**
- 200: Detection results
- 400: Invalid image

#### POST /upload_live_video
Upload video for detection

**Request:**
- Content-Type: multipart/form-data
- Body: video file

**Response:**
- 200: Video processing started
- 400: Invalid video

### Health Endpoints

#### GET /test
Health check endpoint

**Response:**
- 200: Server is running

#### GET /debug
Debug status endpoint

**Response:**
- 200: System status

## Using the API

### cURL Examples

**Login:**
```bash
curl -X POST http://localhost:5000/login \
  -d "username=testuser" \
  -d "password=testpass123"
```

**Register:**
```bash
curl -X POST http://localhost:5000/register \
  -d "username=newuser" \
  -d "email=new@example.com" \
  -d "password=password123" \
  -d "confirm_password=password123"
```

**Get History:**
```bash
curl -X GET http://localhost:5000/history \
  -H "Cookie: session=<your-session-cookie>"
```

### Python Examples

```python
import requests

# Login
response = requests.post('http://localhost:5000/login', data={
    'username': 'testuser',
    'password': 'testpass123'
})
session = response.cookies

# Get history
response = requests.get('http://localhost:5000/history', cookies=session)
print(response.json())
```

## API Response Format

### Success Response
```json
{
  "success": true,
  "data": {
    "vehicle_count": 5,
    "processing_time": "1.23s",
    "breakdown": "Car: 3, Truck: 2"
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error message"
}
```

## Authentication

The API uses session-based authentication. After login, a session cookie is set and must be included in subsequent requests.

## Rate Limiting

Currently, no rate limiting is implemented. Consider adding rate limiting for production use.

## Error Codes

- 200: Success
- 400: Bad Request
- 401: Unauthorized
- 404: Not Found
- 500: Internal Server Error

## Extending API Documentation

To add documentation to a new endpoint:

```python
@app.route('/your-endpoint', methods=['POST'])
def your_endpoint():
    """
    Endpoint Description
    ---
    tags:
      - Your Tag
    parameters:
      - name: param1
        in: formData
        type: string
        required: true
        description: Parameter description
    responses:
      200:
        description: Success
    """
    # Your code here
    pass
```

## OpenAPI Specification

The complete OpenAPI specification is available at:
```
http://localhost:5000/apispec.json
```

You can use this to generate client SDKs in various languages.
