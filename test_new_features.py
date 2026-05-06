"""Test new features: Multi-Camera, Scheduled Detection, Email, Dashboard"""
import sys
sys.path.insert(0, '.')
from web_test_app import app, get_db, User
from werkzeug.security import generate_password_hash
import json

def test_features():
    print('=== Full Feature Testing ===')
    
    # Create test user
    try:
        db = get_db()
        if db:
            user = db.query(User).filter_by(email='test@example.com').first()
            if not user:
                user = User(
                    username='testuser',
                    email='test@example.com',
                    password_hash=generate_password_hash('testpass'),
                    is_active=True
                )
                db.add(user)
                db.commit()
                print('Test user created')
            db.close()
    except Exception as e:
        print(f'User setup: {e}')
    
    with app.test_client() as client:
        # Login
        print('\n1. Login:')
        resp = client.post('/login', data={'email': 'test@example.com', 'password': 'testpass'}, follow_redirects=True)
        print(f'   Status: {resp.status_code}')
        
        # Test Multi-Camera APIs
        print('\n2. Multi-Camera APIs:')
        resp = client.get('/api/multi_camera/status')
        print(f'   /api/multi_camera/status: {resp.status_code}')
        if resp.status_code == 200:
            print(f'   Response: {json.loads(resp.data)}')
        
        print('\n3. Scheduled Detection APIs:')
        resp = client.get('/api/scheduled_detection/tasks')
        print(f'   /api/scheduled_detection/tasks: {resp.status_code}')
        if resp.status_code == 200:
            print(f'   Response: {json.loads(resp.data)}')
        
        # Test Pages
        print('\n4. Page Tests:')
        pages = [
            ('/multi_camera', 'Multi-Camera'),
            ('/scheduled_detection', 'Scheduled'),
            ('/dashboard', 'Analytics'),
        ]
        for url, keyword in pages:
            resp = client.get(url, follow_redirects=True)
            found = keyword in resp.data.decode()
            print(f'   {url}: {resp.status_code} - {keyword} found: {found}')
        
        # Test Scheduled Task Create
        print('\n5. Create Scheduled Task:')
        resp = client.post('/api/scheduled_detection/tasks',
                          json={'task_id': 'test-task', 'interval_seconds': 300, 'source': '0', 'task_type': 'webcam'},
                          content_type='application/json')
        print(f'   Status: {resp.status_code}')
        if resp.status_code == 200:
            print(f'   Response: {json.loads(resp.data)}')
    
    # Test imports
    print('\n6. Module Imports:')
    try:
        from email_service import EmailService
        print('   EmailService: OK')
    except Exception as e:
        print(f'   EmailService: FAIL - {e}')
    
    try:
        from multi_camera import MultiCameraDetector
        print('   MultiCameraDetector: OK')
    except Exception as e:
        print(f'   MultiCameraDetector: FAIL - {e}')
    
    try:
        from scheduled_detection import ScheduledDetectionManager
        print('   ScheduledDetectionManager: OK')
    except Exception as e:
        print(f'   ScheduledDetectionManager: FAIL - {e}')
    
    print('\n=== All Tests Complete ===')

if __name__ == '__main__':
    test_features()
