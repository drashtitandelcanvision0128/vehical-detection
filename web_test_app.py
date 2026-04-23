"""
Vehicle Detection Web Testing App (Flask)
Simple web interface for testing vehicle detection on images/videos
"""

from flask import Flask, render_template_string, request, send_file, flash, redirect, session, url_for
import cv2
import numpy as np
from ultralytics import YOLO
import tempfile
import os
import time
from pathlib import Path
import base64
from io import BytesIO
from fpdf import FPDF
import uuid
from dotenv import load_dotenv
import os
from datetime import datetime
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, Session
from models import Base, ImageDetection, VideoDetection, LiveDetection, DetectionHistory, User
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from collections import defaultdict, deque

# Import authentication templates
try:
    from auth_templates import LOGIN_TEMPLATE, REGISTER_TEMPLATE
except ImportError:
    # Fallback templates with full design
    LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html class="light" lang="en">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>Login - Enterprise Vehicle Intelligence</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
<script id="tailwind-config">
    tailwind.config = {
        darkMode: "class",
        theme: {
            extend: {
                colors: {
                    surface: "#faf9fc",
                    "on-surface": "#1a1c1e",
                    primary: "#002542",
                    "primary-container": "#1b3b5a",
                    "on-primary": "#ffffff",
                    "on-primary-container": "#87a5ca",
                    secondary: "#545f6e",
                    "on-secondary": "#ffffff",
                    "secondary-container": "#d3deef",
                    "on-secondary-container": "#576270",
                    "surface-container": "#eeedf0",
                    "surface-container-low": "#f4f3f6",
                    "surface-container-lowest": "#ffffff",
                    "surface-variant": "#e3e2e5",
                    "on-surface-variant": "#43474d",
                    outline: "#73777e",
                    "outline-variant": "#c3c6ce",
                }
            }
        }
    }
</script>
<style>
    body { font-family: 'Inter', sans-serif; }
    h1, h2, h3, .font-headline { font-family: 'Manrope', sans-serif; }
    .material-symbols-outlined {
        font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
    }
</style>
</head>
<body class="bg-surface text-on-surface min-h-screen flex items-center justify-center p-4">
<div class="w-full max-w-md">
    <div class="bg-surface-container-lowest rounded-xl p-8 shadow-[0px_8px_24px_rgba(0,37,66,0.06)] border border-outline-variant/10">
        <div class="text-center mb-8">
            <div class="flex items-center justify-center gap-3 mb-4">
                <span class="material-symbols-outlined text-primary text-5xl">analytics</span>
            </div>
            <h1 class="text-2xl font-bold text-primary">Enterprise Vehicle Intelligence</h1>
            <p class="text-secondary mt-2">Sign in to access vehicle detection</p>
        </div>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="mb-4 p-4 rounded-lg {% if category == 'error' %}bg-red-50 text-red-800 border border-red-200{% elif category == 'success' %}bg-green-50 text-green-800 border border-green-200{% else %}bg-blue-50 text-blue-800 border border-blue-200{% endif %}">
                        {{ message }}
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        <form method="POST" action="/login">
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-semibold text-primary mb-2">Username</label>
                    <input type="text" name="username" required
                        class="w-full px-4 py-3 rounded-lg border border-outline-variant/40 bg-surface-container-low focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
                        placeholder="Enter your username">
                </div>
                <div>
                    <label class="block text-sm font-semibold text-primary mb-2">Password</label>
                    <input type="password" name="password" required
                        class="w-full px-4 py-3 rounded-lg border border-outline-variant/40 bg-surface-container-low focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
                        placeholder="Enter your password">
                </div>
                <button type="submit"
                    class="w-full h-12 bg-gradient-to-br from-primary to-primary-container text-white font-bold rounded-lg shadow-lg hover:shadow-primary/20 hover:-translate-y-0.5 active:translate-y-0 transition-all flex items-center justify-center gap-2">
                    <span class="material-symbols-outlined">login</span>
                    Sign In
                </button>
            </div>
        </form>
        <div class="mt-6 text-center">
            <p class="text-secondary text-sm">
                Don't have an account? 
                <a href="/register" class="text-primary font-semibold hover:underline">Register here</a>
            </p>
        </div>
    </div>
</div>
</body>
</html>
"""
    REGISTER_TEMPLATE = """
<!DOCTYPE html>
<html class="light" lang="en">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>Register - Enterprise Vehicle Intelligence</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
<script id="tailwind-config">
    tailwind.config = {
        darkMode: "class",
        theme: {
            extend: {
                colors: {
                    surface: "#faf9fc",
                    "on-surface": "#1a1c1e",
                    primary: "#002542",
                    "primary-container": "#1b3b5a",
                    "on-primary": "#ffffff",
                    "on-primary-container": "#87a5ca",
                    secondary: "#545f6e",
                    "on-secondary": "#ffffff",
                    "secondary-container": "#d3deef",
                    "on-secondary-container": "#576270",
                    "surface-container": "#eeedf0",
                    "surface-container-low": "#f4f3f6",
                    "surface-container-lowest": "#ffffff",
                    "surface-variant": "#e3e2e5",
                    "on-surface-variant": "#43474d",
                    outline: "#73777e",
                    "outline-variant": "#c3c6ce",
                }
            }
        }
    }
</script>
<style>
    body { font-family: 'Inter', sans-serif; }
    h1, h2, h3, .font-headline { font-family: 'Manrope', sans-serif; }
    .material-symbols-outlined {
        font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
    }
</style>
</head>
<body class="bg-surface text-on-surface min-h-screen flex items-center justify-center p-4">
<div class="w-full max-w-md">
    <div class="bg-surface-container-lowest rounded-xl p-8 shadow-[0px_8px_24px_rgba(0,37,66,0.06)] border border-outline-variant/10">
        <div class="text-center mb-8">
            <div class="flex items-center justify-center gap-3 mb-4">
                <span class="material-symbols-outlined text-primary text-5xl">analytics</span>
            </div>
            <h1 class="text-2xl font-bold text-primary">Enterprise Vehicle Intelligence</h1>
            <p class="text-secondary mt-2">Create your account</p>
        </div>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="mb-4 p-4 rounded-lg {% if category == 'error' %}bg-red-50 text-red-800 border border-red-200{% elif category == 'success' %}bg-green-50 text-green-800 border border-green-200{% else %}bg-blue-50 text-blue-800 border border-blue-200{% endif %}">
                        {{ message }}
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        <form method="POST" action="/register">
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-semibold text-primary mb-2">Username</label>
                    <input type="text" name="username" required
                        class="w-full px-4 py-3 rounded-lg border border-outline-variant/40 bg-surface-container-low focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
                        placeholder="Choose a username">
                </div>
                <div>
                    <label class="block text-sm font-semibold text-primary mb-2">Email</label>
                    <input type="email" name="email" required
                        class="w-full px-4 py-3 rounded-lg border border-outline-variant/40 bg-surface-container-low focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
                        placeholder="Enter your email">
                </div>
                <div>
                    <label class="block text-sm font-semibold text-primary mb-2">Password</label>
                    <input type="password" name="password" required minlength="6"
                        class="w-full px-4 py-3 rounded-lg border border-outline-variant/40 bg-surface-container-low focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
                        placeholder="Create a password (min 6 characters)">
                </div>
                <div>
                    <label class="block text-sm font-semibold text-primary mb-2">Confirm Password</label>
                    <input type="password" name="confirm_password" required minlength="6"
                        class="w-full px-4 py-3 rounded-lg border border-outline-variant/40 bg-surface-container-low focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
                        placeholder="Confirm your password">
                </div>
                <button type="submit"
                    class="w-full h-12 bg-gradient-to-br from-primary to-primary-container text-white font-bold rounded-lg shadow-lg hover:shadow-primary/20 hover:-translate-y-0.5 active:translate-y-0 transition-all flex items-center justify-center gap-2">
                    <span class="material-symbols-outlined">person_add</span>
                    Create Account
                </button>
            </div>
        </form>
        <div class="mt-6 text-center">
            <p class="text-secondary text-sm">
                Already have an account? 
                <a href="/login" class="text-primary font-semibold hover:underline">Sign in here</a>
            </p>
        </div>
    </div>
</div>
</body>
</html>
"""

app = Flask(__name__)
app.secret_key = 'vehicle-detection-secret-key'

# Authentication decorator
def login_required(f):
    """Decorator to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # Check if it's an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return {'success': False, 'error': 'Not logged in'}, 401
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Load environment variables
load_dotenv()

# SQLAlchemy setup
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///vehical_detections.db')

engine = None
SessionLocal = None

def init_db():
    """Initialize database connection and create tables"""
    global engine, SessionLocal, DATABASE_URL
    try:
        # Use SQLite directly
        if 'sqlite' in DATABASE_URL:
            engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
        else:
            engine = create_engine(DATABASE_URL, pool_size=20, max_overflow=10)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print(f"[INFO] Database connection established: {DATABASE_URL}")
        print("[INFO] Tables created successfully")
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        import traceback
        traceback.print_exc()
        engine = None
        SessionLocal = None

def get_db():
    """Get database session"""
    if SessionLocal is None:
        return None
    return SessionLocal()

# Authentication Routes (defined after get_db() is available)
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        db = get_db()
        if not db:
            flash('Database connection error. Please try again.', 'error')
            return render_template_string(LOGIN_TEMPLATE)
        
        try:
            user = db.query(User).filter(User.username == username).first()
            if user and check_password_hash(user.password_hash, password):
                session['user_id'] = user.id
                session['username'] = user.username
                flash('Login successful!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password.', 'error')
        except Exception as e:
            print(f"[ERROR] Login error: {e}")
            flash('Login failed. Please try again.', 'error')
        finally:
            db.close()
    
    return render_template_string(LOGIN_TEMPLATE)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page"""
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return render_template_string(REGISTER_TEMPLATE)
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template_string(REGISTER_TEMPLATE)
        
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template_string(REGISTER_TEMPLATE)
        
        db = get_db()
        if not db:
            flash('Database connection error. Please try again.', 'error')
            return render_template_string(REGISTER_TEMPLATE)
        
        try:
            existing_user = db.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first()
            
            if existing_user:
                flash('Username or email already exists.', 'error')
                return render_template_string(REGISTER_TEMPLATE)
            
            new_user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                is_active=1
            )
            db.add(new_user)
            db.commit()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            print(f"[ERROR] Registration error: {e}")
            db.rollback()
            flash('Registration failed. Please try again.', 'error')
        finally:
            db.close()
    
    return render_template_string(REGISTER_TEMPLATE)


@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

def save_detection_to_db(report_id, timestamp, input_type, message, stats, image_data, video_path, conf_threshold):
    """Save detection result to database using SQLAlchemy"""
    print(f"[DEBUG] save_detection_to_db called: report_id={report_id}, input_type={input_type}")
    print(f"[DEBUG] Stats received: {stats}, type: {type(stats)}")

    db = get_db()
    if not db:
        print("[WARN] Could not get database session, using memory fallback")
        return False

    try:
        user_id = session.get('user_id')
        # Ensure stats is a dict
        if isinstance(stats, str):
            try:
                import json
                stats = json.loads(stats)
                print(f"[DEBUG] Stats converted from string to dict")
            except Exception as e:
                print(f"[DEBUG] Failed to parse stats as JSON: {e}")
                stats = {}
        elif not isinstance(stats, dict):
            stats = {}

        vehicle_count = stats.get('count', 0) if stats else 0
        processing_time = stats.get('time', '') if stats else ''
        breakdown = stats.get('breakdown', '') if isinstance(stats, dict) else ''

        # Convert breakdown dict to string for database storage
        if isinstance(breakdown, dict):
            breakdown_str = ', '.join([f"{k}: {v}" for k, v in breakdown.items()])
        else:
            breakdown_str = str(breakdown) if breakdown else ''

        print(f"[DEBUG] Saving detection: count={vehicle_count}, type={input_type}")

        # Save to specific table based on type (use merge to handle duplicates)
        if input_type == 'video':
            existing = db.query(VideoDetection).filter_by(report_id=report_id).first()
            if existing:
                existing.timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                existing.message = message
                existing.vehicle_count = vehicle_count
                existing.processing_time = processing_time
                existing.confidence_threshold = conf_threshold
                existing.video_path = video_path
                existing.stats = stats
                existing.breakdown = breakdown_str
                existing.user_id = user_id
            else:
                detection = VideoDetection(
                    report_id=report_id,
                    timestamp=datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S'),
                    message=message,
                    vehicle_count=vehicle_count,
                    processing_time=processing_time,
                    confidence_threshold=conf_threshold,
                    video_path=video_path,
                    stats=stats,
                    breakdown=breakdown_str,
                    user_id=user_id
                )
                db.add(detection)
        else:
            existing = db.query(ImageDetection).filter_by(report_id=report_id).first()
            if existing:
                existing.timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                existing.message = message
                existing.vehicle_count = vehicle_count
                existing.processing_time = processing_time
                existing.confidence_threshold = conf_threshold
                existing.image_data = image_data
                existing.stats = stats
                existing.breakdown = breakdown_str
                existing.user_id = user_id
            else:
                detection = ImageDetection(
                    report_id=report_id,
                    timestamp=datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S'),
                    message=message,
                    vehicle_count=vehicle_count,
                    processing_time=processing_time,
                    confidence_threshold=conf_threshold,
                    image_data=image_data,
                    stats=stats,
                    breakdown=breakdown_str,
                    user_id=user_id
                )
                db.add(detection)

        # Also save to unified history table (simplified - only report data)
        existing_history = db.query(DetectionHistory).filter_by(report_id=report_id).first()
        if existing_history:
            existing_history.detection_type = input_type
            existing_history.timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            existing_history.vehicle_count = vehicle_count
            existing_history.processing_time = processing_time
            existing_history.confidence_threshold = conf_threshold
            existing_history.breakdown = breakdown_str
            existing_history.image_data = image_data if input_type == 'image' else None
            existing_history.video_path = video_path if input_type == 'video' else None
            existing_history.user_id = user_id
        else:
            history_entry = DetectionHistory(
                report_id=report_id,
                detection_type=input_type,
                timestamp=datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S'),
                vehicle_count=vehicle_count,
                processing_time=processing_time,
                confidence_threshold=conf_threshold,
                breakdown=breakdown_str,
                image_data=image_data if input_type == 'image' else None,
                video_path=video_path if input_type == 'video' else None,
                user_id=user_id
            )
            db.add(history_entry)

        db.commit()
        print(f"[INFO] Detection saved to database: {report_id}, type={input_type}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save detection to database: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise  # Re-raise so caller can report the actual error
    finally:
        db.close()

def get_detection_history_from_db(limit=50):
    """Fetch detection history from unified history table using SQLAlchemy"""
    db = get_db()
    if not db:
        print("[WARN] Could not get database session, using memory fallback")
        return app.detection_history[:limit]

    try:
        # Get user_id from session
        user_id = session.get('user_id')
        print(f"[DEBUG] Fetching history for user_id: {user_id}")
        
        # Get detections filtered by user_id from unified history table
        query = db.query(DetectionHistory).order_by(DetectionHistory.timestamp.desc())
        if user_id:
            query = query.filter(DetectionHistory.user_id == user_id)
        history_records = query.limit(limit).all()

        # Convert to history format
        history = []
        for record in history_records:
            history.append({
                'id': record.report_id,
                'timestamp': record.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'input_type': record.detection_type,
                'detection_type': record.detection_type,
                'message': '',
                'stats': {'count': record.vehicle_count, 'time': record.processing_time},
                'image': record.image_data,
                'image_data': record.image_data,  # Add both keys for compatibility
                'video_path': record.video_path,
                'vehicle_count': record.vehicle_count,
                'breakdown': record.breakdown
            })

        print(f"[INFO] Fetched {len(history)} records from unified history table")
        return history
    except Exception as e:
        print(f"[ERROR] Failed to fetch history from database: {e}")
        return app.detection_history[:limit]
    finally:
        db.close()

def save_live_detection_to_db(report_id, session_start, session_end, total_detections, conf_threshold, stats, breakdown, image_data=None, video_path=None):
    """Save live detection session to database"""
    print(f"[DEBUG] save_live_detection_to_db called: report_id={report_id}, video_path={video_path}")
    db = get_db()
    if not db:
        print("[WARN] Could not get database session, using memory fallback")
        return False

    try:
        user_id = session.get('user_id')
        # Save to live_detections table (handle duplicates)
        existing = db.query(LiveDetection).filter_by(report_id=report_id).first()
        if existing:
            existing.timestamp = datetime.utcnow()
            existing.session_start = session_start
            existing.session_end = session_end
            existing.total_detections = total_detections
            existing.confidence_threshold = conf_threshold
            existing.stats = stats
            existing.breakdown = breakdown
            existing.user_id = user_id
            print(f"[DEBUG] Updated existing live detection record: {report_id}")
        else:
            live_detection = LiveDetection(
                report_id=report_id,
                timestamp=datetime.utcnow(),
                session_start=session_start,
                session_end=session_end,
                total_detections=total_detections,
                confidence_threshold=conf_threshold,
                stats=stats,
                breakdown=breakdown,
                user_id=user_id
            )
            db.add(live_detection)
            print(f"[DEBUG] Created new live detection record: {report_id}")

        # Also save to detection_history table with video_path
        history_existing = db.query(DetectionHistory).filter_by(report_id=report_id).first()
        if history_existing:
            history_existing.timestamp = datetime.utcnow()
            history_existing.vehicle_count = total_detections
            history_existing.confidence_threshold = conf_threshold
            history_existing.breakdown = breakdown
            history_existing.image_data = image_data
            history_existing.video_path = video_path
            history_existing.user_id = user_id
            print(f"[DEBUG] Updated existing history record: {report_id}, video_path={video_path}")
        else:
            history = DetectionHistory(
                report_id=report_id,
                detection_type='live',
                timestamp=datetime.utcnow(),
                vehicle_count=total_detections,
                confidence_threshold=conf_threshold,
                breakdown=breakdown,
                image_data=image_data,
                video_path=video_path,
                user_id=user_id
            )
            db.add(history)
            print(f"[DEBUG] Created new history record: {report_id}, video_path={video_path}")

        db.commit()
        print(f"[INFO] Live detection saved to database: {report_id}, video_path={video_path}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save live detection to database: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        if db:
            db.close()

# Store detection results for PDF generation (keyed by report_id)
app.stored_results = {}

# Store detection history (fallback if DB not available)
app.detection_history = []

# Increase max upload size to 500MB for large video uploads
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

# Create static directory for processed videos
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'videos')
os.makedirs(STATIC_DIR, exist_ok=True)
print(f"[INFO] Video output directory: {STATIC_DIR}")

# Vehicle-only classes from COCO dataset
VEHICLE_CLASSES = {
    2: 'car',
    3: 'motorcycle',  # Includes bikes, scooters, scooty
    5: 'bus',
    7: 'truck'
}

# Colors for each vehicle class (BGR for OpenCV)
CLASS_COLORS = {
    'car': (0, 255, 0),           # Green
    'motorcycle': (255, 0, 255),  # Magenta (includes bikes, scooty)
    'bus': (0, 255, 255),         # Yellow
    'truck': (0, 0, 255)          # Red
}

# Display names for UI (with scooty included)
DISPLAY_NAMES = {
    'car': 'Car',
    'motorcycle': 'Motorcycle/Scooty',
    'bus': 'Bus',
    'truck': 'Truck'
}

# Vehicle Tracker for counting
class VehicleTracker:
    """Track vehicles across frames for line crossing counting"""
    
    def __init__(self, max_disappeared=30, max_distance=50):
        self.next_id = 0
        self.vehicles = {}
        self.disappeared = {}
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance
        self.count_up = 0
        self.count_down = 0
        self.counted_ids = set()
        
    def calculate_center(self, bbox):
        """Calculate center point of bounding box"""
        x1, y1, x2, y2 = bbox
        return ((x1 + x2) // 2, (y1 + y2) // 2)
    
    def calculate_distance(self, p1, p2):
        """Calculate Euclidean distance between two points"""
        return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
    
    def register(self, bbox, class_name):
        """Register a new vehicle"""
        self.vehicles[self.next_id] = {
            'bbox': bbox,
            'center': self.calculate_center(bbox),
            'class': class_name,
            'positions': deque(maxlen=10),
            'first_seen': time.time()
        }
        self.vehicles[self.next_id]['positions'].append(self.calculate_center(bbox))
        self.disappeared[self.next_id] = 0
        self.next_id += 1
        return self.next_id - 1
    
    def deregister(self, vehicle_id):
        """Remove a vehicle from tracking"""
        del self.vehicles[vehicle_id]
        del self.disappeared[vehicle_id]
    
    def update(self, detections, count_line_y=None, frame_height=None):
        """Update tracker with new detections"""
        if len(detections) == 0:
            for vehicle_id in list(self.disappeared.keys()):
                self.disappeared[vehicle_id] += 1
                if self.disappeared[vehicle_id] > self.max_disappeared:
                    self.deregister(vehicle_id)
            return self.vehicles
        
        input_centers = []
        for det in detections:
            center = self.calculate_center(det['box'])
            input_centers.append((center, det))
        
        if len(self.vehicles) == 0:
            for center, det in input_centers:
                self.register(det['box'], det['class_name'])
        else:
            vehicle_ids = list(self.vehicles.keys())
            vehicle_centers = [self.vehicles[v_id]['center'] for v_id in vehicle_ids]
            
            used = set()
            for center, det in input_centers:
                min_dist = float('inf')
                closest_id = None
                
                for v_id in vehicle_centers:
                    if v_id in used:
                        continue
                    dist = self.calculate_distance(center, vehicle_centers[v_id])
                    if dist < min_dist and dist < self.max_distance:
                        min_dist = dist
                        closest_id = v_id
                
                if closest_id is not None:
                    used.add(closest_id)
                    self.vehicles[closest_id]['bbox'] = det['box']
                    self.vehicles[closest_id]['center'] = center
                    self.vehicles[closest_id]['positions'].append(center)
                    self.disappeared[closest_id] = 0
                    
                    # Check line crossing
                    if count_line_y and closest_id not in self.counted_ids:
                        prev_center = self.vehicles[closest_id]['positions'][0] if len(self.vehicles[closest_id]['positions']) > 1 else center
                        
                        # Check if crossed the line
                        if prev_center[1] < count_line_y and center[1] >= count_line_y:
                            self.count_down += 1
                            self.counted_ids.add(closest_id)
                        elif prev_center[1] > count_line_y and center[1] <= count_line_y:
                            self.count_up += 1
                            self.counted_ids.add(closest_id)
                else:
                    self.register(det['box'], det['class_name'])
            
            # Mark unused vehicles as disappeared
            for v_id in vehicle_ids:
                if v_id not in used:
                    self.disappeared[v_id] += 1
                    if self.disappeared[v_id] > self.max_disappeared:
                        self.deregister(v_id)
        
        return self.vehicles

# Global tracker instance
vehicle_tracker = VehicleTracker()

# Check ffmpeg availability
print("[INFO] Checking ffmpeg availability...")
try:
    import subprocess
    ffmpeg_result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
    if ffmpeg_result.returncode == 0:
        print("[SUCCESS] ffmpeg found - videos will be converted to H264 for browser playback")
    else:
        print("[WARN] ffmpeg not available - videos may not play in browser (only download)")
        print("[INFO] To fix: Install ffmpeg and add to PATH")
except FileNotFoundError:
    print("[WARN] ffmpeg not found - videos may not play in browser (only download)")
    print("[INFO] To fix: Install ffmpeg and add to PATH")
except Exception as e:
    print(f"[WARN] Could not check ffmpeg: {e}")

# Load model
print("[INFO] Loading YOLOv8n model...")
model = YOLO('yolov8n.pt')
print("[INFO] Model ready!")

# HTML Template - Modern Design Matching Image
HTML_TEMPLATE = """
<!DOCTYPE html>
<html class="light" lang="en">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>Enterprise Vehicle Intelligence</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&amp;family=Inter:wght@400;500;600;700&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<script id="tailwind-config">
        tailwind.config = {
            darkMode: "class",
            theme: {
                extend: {
                    "colors": {
                        "surface-variant": "#e3e2e5",
                        "tertiary-container": "#4f3303",
                        "surface": "#faf9fc",
                        "on-secondary-fixed": "#121c28",
                        "primary-container": "#1b3b5a",
                        "tertiary-fixed-dim": "#ecbf83",
                        "on-error-container": "#93000a",
                        "surface-container": "#eeedf0",
                        "on-error": "#ffffff",
                        "primary-fixed-dim": "#abc9ef",
                        "on-tertiary-fixed-variant": "#5f4110",
                        "on-surface-variant": "#43474d",
                        "error-container": "#ffdad6",
                        "on-background": "#1a1c1e",
                        "on-primary-container": "#87a5ca",
                        "secondary-container": "#d3deef",
                        "primary-fixed": "#d1e4ff",
                        "on-primary-fixed": "#001d35",
                        "on-surface": "#1a1c1e",
                        "surface-tint": "#436182",
                        "on-tertiary": "#ffffff",
                        "surface-container-low": "#f4f3f6",
                        "secondary": "#545f6e",
                        "tertiary-fixed": "#ffddb3",
                        "on-tertiary-fixed": "#291800",
                        "outline": "#73777e",
                        "surface-dim": "#dad9dd",
                        "outline-variant": "#c3c6ce",
                        "on-secondary": "#ffffff",
                        "surface-container-high": "#e9e8eb",
                        "tertiary": "#341f00",
                        "on-tertiary-container": "#c59c63",
                        "surface-container-lowest": "#ffffff",
                        "secondary-fixed": "#d8e3f4",
                        "inverse-primary": "#abc9ef",
                        "on-primary": "#ffffff",
                        "inverse-on-surface": "#f1f0f3",
                        "on-secondary-container": "#576270",
                        "error": "#ba1a1a",
                        "secondary-fixed-dim": "#bcc7d8",
                        "on-secondary-fixed-variant": "#3d4855",
                        "primary": "#002542",
                        "inverse-surface": "#2f3033",
                        "on-primary-fixed-variant": "#2a4968",
                        "surface-container-highest": "#e3e2e5",
                        "background": "#faf9fc",
                        "surface-bright": "#faf9fc"
                    },
                    "borderRadius": {
                        "DEFAULT": "0.125rem",
                        "lg": "0.25rem",
                        "xl": "0.5rem",
                        "full": "0.75rem"
                    },
                    "fontFamily": {
                        "headline": ["Manrope"],
                        "body": ["Inter"],
                        "label": ["Inter"]
                    }
                },
            },
        }
    </script>
<style>
        body { font-family: 'Inter', sans-serif; }
        h1, h2, h3, .font-headline { font-family: 'Manrope', sans-serif; }
        .material-symbols-outlined {
            font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
        }
        .glass-panel {
            background: rgba(250, 249, 252, 0.7);
            backdrop-filter: blur(12px);
        }
        .glass-hud {
            background: rgba(250, 249, 252, 0.7);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(195, 198, 206, 0.2);
        }
        .gradient-button {
            background: linear-gradient(135deg, #002542 0%, #1b3b5a 100%);
        }
        @keyframes loading {
            0% { transform: translateX(-100%); }
            50% { transform: translateX(0%); }
            100% { transform: translateX(100%); }
        }
    </style>
</head>
<body class="bg-surface text-on-surface min-h-screen">
<!-- TopAppBar -->
<header class="fixed top-0 w-full z-50 bg-slate-50/70 backdrop-blur-md shadow-[0px_8px_24px_rgba(0,37,66,0.06)] flex items-center justify-between px-6 h-16 w-full">
<div class="flex items-center gap-3">
<span class="material-symbols-outlined text-blue-900">analytics</span>
<span class="text-xl font-bold tracking-tight text-blue-900">Enterprise Vehicle Intelligence</span>
</div>
<div class="flex items-center gap-6">
<nav class="hidden md:flex gap-6">
<a class="text-blue-900 font-semibold text-sm" href="/">Upload</a>
<a class="text-slate-500 hover:bg-blue-50 transition-colors px-3 py-1 rounded-lg text-sm" href="/live">Real-time</a>
<a class="text-slate-500 hover:bg-blue-50 transition-colors px-3 py-1 rounded-lg text-sm" href="/history">History</a>
</nav>
<div class="flex items-center gap-3 border-l border-outline-variant/20 pl-6">
<div class="flex items-center gap-2">
<span class="material-symbols-outlined text-primary text-sm">account_circle</span>
<span class="text-sm font-semibold text-primary">{{ session.get('username', 'User') }}</span>
</div>
<a href="/logout" class="flex items-center gap-1 text-sm text-red-600 hover:text-red-700 hover:bg-red-50 transition-colors px-3 py-1.5 rounded-lg font-semibold">
<span class="material-symbols-outlined text-sm">logout</span>
Logout
</a>
</div>
</div>
</header>
<main class="pt-24 pb-12 px-6 max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8">
<!-- Left Column: Instructions & Info -->
<div class="lg:col-span-4 space-y-8">
<header>
<h1 class="text-[2.75rem] font-extrabold leading-tight tracking-tight text-primary">Vehicle Detection Testing App</h1>
<p class="mt-4 text-title-md text-secondary leading-relaxed">Upload or paste an image to detect vehicles using our laboratory-grade neural network.</p>
</header>
<!-- Info Box: Detection Scope -->
<section class="bg-surface-container-low rounded-xl p-6 space-y-6">
<div>
<h3 class="text-label-md font-bold text-primary uppercase tracking-wider mb-4 flex items-center gap-2">
<span class="material-symbols-outlined text-sm">check_circle</span>
                        Detection Targets
                    </h3>
<div class="grid grid-cols-2 gap-3">
<div class="bg-surface-container-lowest p-3 rounded-lg border border-outline-variant/10">
<span class="text-sm font-semibold text-on-surface">Car</span>
</div>
<div class="bg-surface-container-lowest p-3 rounded-lg border border-outline-variant/10">
<span class="text-sm font-semibold text-on-surface">Motorcycle</span>
</div>
<div class="bg-surface-container-lowest p-3 rounded-lg border border-outline-variant/10">
<span class="text-sm font-semibold text-on-surface">Bus</span>
</div>
<div class="bg-surface-container-lowest p-3 rounded-lg border border-outline-variant/10">
<span class="text-sm font-semibold text-on-surface">Truck</span>
</div>
</div>
</div>
<div class="pt-4 border-t border-outline-variant/20">
<h3 class="text-label-md font-bold text-slate-500 uppercase tracking-wider mb-4 flex items-center gap-2">
<span class="material-symbols-outlined text-sm">block</span>
                        Excluded Classes
                    </h3>
<p class="text-sm text-secondary leading-relaxed">
                        The current model iteration ignores non-vehicular entities including people, animals, vegetation, and static infrastructure to ensure high precision in traffic flow analysis.
                    </p>
</div>
</section>
</div>
<!-- Right Column: Testing Interface -->
<div class="lg:col-span-8 space-y-6 text-center">
<!-- Main Upload Area -->
<div class="bg-surface-container-lowest rounded-xl p-8 shadow-[0px_8px_24px_rgba(0,37,66,0.06)] border border-outline-variant/10">
<div class="relative group cursor-pointer border-2 border-dashed border-outline-variant/40 rounded-xl transition-all hover:border-primary/40 hover:bg-surface-container-low flex flex-col items-center justify-center min-h-[300px] text-center p-12" id="dragDropArea">
<div class="w-20 h-20 bg-primary-fixed rounded-full flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
<span class="material-symbols-outlined text-primary text-4xl">cloud_upload</span>
</div>
<h2 class="text-xl font-bold text-primary mb-2">Upload Image or Video</h2>
<p class="text-secondary max-w-sm">Drag and drop your media here, or browse local files. Supports JPG, PNG, MP4 up to 50MB.</p>
<div id="selectedFileDisplay" style="display: none; margin: 10px 0; padding: 10px; background: #e3f2fd; border-radius: 5px; color: #1976D2;">
<strong>Selected:</strong> <span id="fileName"></span>
</div>
</div>
</div>
<form action="/" method="POST" enctype="multipart/form-data" id="uploadForm" class="text-center mt-6">
<input type="file" name="file" id="fileInput" accept=".jpg,.jpeg,.png,.mp4,.avi,.mov" style="display: none;">
<input type="hidden" name="pasted_image" id="pastedImageData">
<div class="flex flex-wrap justify-center gap-4">
<button type="button" class="flex items-center gap-2 px-6 py-2.5 bg-surface-container-high text-primary font-semibold rounded-lg hover:bg-surface-variant transition-colors" id="copyPasteBtn" onclick="enablePasteMode()">
<span class="material-symbols-outlined text-xl">content_paste</span>
                            Paste Image
                        </button>
<button type="button" class="flex items-center gap-2 px-6 py-2.5 bg-surface-container-high text-primary font-semibold rounded-lg hover:bg-surface-variant transition-colors" id="webcamBtn" onclick="window.location.href='/live'">
<span class="material-symbols-outlined text-xl">videocam</span>
                            Live Webcam
                        </button>
</div>
<p id="pasteInstructions" style="color: #2196F3; font-size: 14px; display: none; margin-top: 10px; text-align: center;">
                    Paste mode active! Press Ctrl+V to paste image from clipboard
                </p>
<p id="webcamInstructions" style="color: #9C27B0; font-size: 14px; display: none; margin-top: 10px; text-align: center;">
                    Webcam active! Close this tab or click Stop to end detection
                </p>
<!-- Pasted Image Preview -->
<div id="pastePreviewContainer" style="display: none; margin-top: 20px; padding: 10px; border: 2px solid #4CAF50; border-radius: 5px;">
<p style="color: #4CAF50; font-weight: bold; margin-bottom: 10px;">Image ready for detection:</p>
<img id="pastedPreview" style="max-width: 100%; max-height: 300px; border-radius: 5px;" alt="Pasted image preview">
<button type="button" onclick="clearPastedImage()" style="margin-top: 10px; background: #f44336; color: white; padding: 5px 15px; border: none; border-radius: 3px; cursor: pointer;">
                    Clear Image
                </button>
</div>
<!-- Controls Section -->
<div class="mt-8 grid grid-cols-1 gap-8 items-end flex justify-center">
<div class="flex justify-center">
<button type="submit" class="h-14 bg-gradient-to-br from-primary to-primary-container text-white font-bold rounded-lg shadow-lg hover:shadow-primary/20 hover:-translate-y-0.5 active:translate-y-0 transition-all flex items-center justify-center gap-3 min-w-[240px] px-8" id="detectBtn">
<span class="material-symbols-outlined">analytics</span>
                            Detect Vehicles
                        </button>
</div>
</div>
</form>
<!-- Bento Preview Section -->
<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
<div class="md:col-span-2 bg-surface-container-high rounded-xl overflow-hidden aspect-video relative">
<video class="w-full h-full object-cover" id="demoVideo" muted loop playsinline controls>
<source src="/static/demo_converted.mp4" type="video/mp4">
Your browser does not support the video tag.
</video>
</div>
<div class="bg-primary text-primary-fixed p-6 rounded-xl flex flex-col justify-between">
<span class="material-symbols-outlined text-4xl" style="font-variation-settings: 'FILL' 1;">bolt</span>
<div>
<p class="text-label-md font-bold uppercase tracking-widest opacity-60">Avg. Inference</p>
<p class="text-3xl font-bold font-headline">14.2ms</p>
</div>
</div>
<!-- Webcam Section -->
<div id="webcamSection" style="display: none; margin: 0; padding: 0; border: none; background: #000; width: 100%; min-height: 80vh; position: fixed; top: 64px; left: 0; right: 0; z-index: 100;">
<div style="display: flex; justify-content: space-between; align-items: center; padding: 15px 20px; background: rgba(156, 39, 176, 0.9); position: absolute; top: 0; left: 0; right: 0; z-index: 101;">
<div style="display: flex; align-items: center; gap: 15px;">
<h3 style="color: white; margin: 0;">Live Webcam Detection</h3>
<div id="detectionStatusBadge" style="padding: 5px 15px; border-radius: 20px; font-size: 14px; font-weight: bold; background: #FFC107; color: #333;">
                        Waiting...
                    </div>
</div>
<button type="button" onclick="stopWebcam()" style="background: #f44336; color: white; padding: 8px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 14px;">
                    Stop Webcam
                </button>
</div>
<div style="display: flex; gap: 20px; flex-wrap: wrap; width: 100%; height: 100%; padding-top: 50px;">
<div style="flex: 1; min-width: 50%;">
<p style="color: white; font-weight: bold; margin-bottom: 5px; padding-left: 20px;">Original Feed:</p>
<video id="webcamVideo" autoplay playsinline style="width: 100%; height: calc(100vh - 150px); object-fit: contain; background: #000;"></video>
</div>
<div style="flex: 1; min-width: 50%;">
<p style="color: white; font-weight: bold; margin-bottom: 5px; padding-left: 20px;">Detection Output:</p>
<canvas id="detectionCanvas" style="width: 100%; height: calc(100vh - 150px); object-fit: contain; background: #000;"></canvas>
</div>
</div>
<div id="webcamStats" style="margin-top: 15px; padding: 15px; background: white; border-radius: 5px; border-left: 5px solid #9C27B0;">
<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
<div>
<strong style="color: #333;">Detection Status:</strong> 
<span id="webcamStatsText" style="color: #666; font-size: 16px;">Waiting for frames...</span>
</div>
<div id="detectionActivity" style="padding: 8px 15px; border-radius: 5px; font-weight: bold; background: #f5f5f5; color: #666;">
                        No vehicles detected
                    </div>
</div>
<div style="margin-top: 10px; font-size: 13px; color: #999;">
<strong>Tip:</strong> Point camera at vehicles to see detection boxes. Green boxes = detected vehicles.
                </div>
</div>
</div>
<!-- Result Section - Detection Analysis -->
{% if result %}
<div class="fixed inset-0 bg-surface z-50 overflow-y-auto" style="display: none;" id="resultModal">
<!-- TopAppBar -->
<header class="sticky top-0 z-50 bg-slate-50/70 backdrop-blur-md shadow-[0px_8px_24px_rgba(0,37,66,0.06)] flex items-center justify-between px-6 h-16">
<div class="flex items-center gap-3">
<button class="material-symbols-outlined text-blue-900 active:scale-95 duration-200 hover:bg-blue-50 p-2 rounded-full" onclick="closeResultModal()">arrow_back</button>
<span class="material-symbols-outlined text-blue-900">analytics</span>
<span class="text-xl font-bold tracking-tight text-blue-900">Enterprise Vehicle Intelligence</span>
</div>
<div class="flex items-center gap-6">
<nav class="hidden md:flex gap-6">
<a class="text-slate-500 hover:bg-blue-50 transition-colors px-3 py-1 rounded-lg text-sm" href="/">Upload</a>
<a class="text-slate-500 hover:bg-blue-50 transition-colors px-3 py-1 rounded-lg text-sm" href="/live">Real-time</a>
<a class="text-slate-500 hover:bg-blue-50 transition-colors px-3 py-1 rounded-lg text-sm" href="/history">History</a>
</nav>
</div>
</header>
<main class="max-w-7xl mx-auto px-4 md:px-8 py-8">
<!-- Layout Grid -->
<div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
<!-- Left Column: Image View (Bento Large) -->
<div class="lg:col-span-8 space-y-6">
<div class="relative bg-surface-container-lowest rounded-xl overflow-hidden shadow-[0px_8px_24px_rgba(0,37,66,0.06)] group">
{% if result.image %}
<img alt="Vehicle detection analysis" class="w-full h-auto object-cover aspect-video" src="data:image/jpeg;base64,{{ result.image }}"/>
{% elif result.stats and result.stats.first_frame %}
<img alt="Vehicle detection analysis" class="w-full h-auto object-cover aspect-video" src="data:image/jpeg;base64,{{ result.stats.first_frame }}"/>
{% endif %}
<!-- Detection Overlays (Simulated) -->
<div class="absolute inset-0 pointer-events-none">
<div class="absolute top-[25%] left-[30%] w-[18%] h-[22%] border-2 border-primary-fixed flex items-start">
<span class="bg-primary px-2 py-0.5 text-[10px] font-mono text-white flex items-center gap-1">
<span class="material-symbols-outlined text-[12px]" style="font-variation-settings: 'FILL' 1;">directions_car</span>
                                Car - 98%
                            </span>
</div>
<div class="absolute inset-0 bg-gradient-to-b from-transparent via-primary/5 to-transparent h-1/4 w-full opacity-30"></div>
</div>
<!-- Live Indicators -->
<div class="absolute top-4 right-4 glass-hud px-4 py-2 rounded-lg flex items-center gap-3">
<div class="flex items-center gap-2">
<span class="w-2 h-2 rounded-full bg-error animate-pulse"></span>
<span class="text-[10px] font-bold uppercase tracking-widest text-on-surface">Live Stream</span>
</div>
<div class="h-4 w-[1px] bg-outline-variant/30"></div>
<span class="text-[10px] font-mono text-on-surface-variant">04:12:44:09</span>
</div>
</div>
<!-- Inference Metrics (Horizontal technical bar) -->
<div class="bg-surface-container-low p-6 rounded-xl flex flex-wrap gap-8 items-center border border-outline-variant/10">
<div>
<p class="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant mb-1">Processing Time</p>
<p class="text-primary font-mono font-bold">{% if result.stats %}{{ result.stats.time }}{% else %}--{% endif %}</p>
</div>
<div class="w-[1px] h-8 bg-outline-variant/20 hidden md:block"></div>
<div>
<p class="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant mb-1">Model Architecture</p>
<p class="text-primary font-mono font-bold">YOLOv8 Laboratory Grade</p>
</div>
<div class="w-[1px] h-8 bg-outline-variant/20 hidden md:block"></div>
<div>
<p class="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant mb-1">Inference Device</p>
<p class="text-primary font-mono font-bold">GPU Acceleration (A100)</p>
</div>
</div>
{% if result.video_path %}
<!-- Video Player -->
<div class="bg-gray-900 rounded-lg p-4 text-center">
<p class="text-white font-bold mb-3">Full Video with Detection:</p>
<video width="100%" height="auto" controls 
class="max-h-96 rounded-lg"
preload="metadata"
style="max-height: 400px;">
<source src="/view/{{ result.video_path }}?t={{ result.timestamp }}" type="video/mp4">
<p class="text-white py-8">
Your browser does not support video playback.<br>
Use the buttons below to view or download.
</p>
</video>
</div>
<div class="mt-4 flex gap-3 flex-wrap justify-center">
<a href="/view/{{ result.video_path }}?t={{ result.timestamp }}" target="_blank" 
class="px-6 py-3 bg-green-600 text-white font-bold rounded-lg hover:bg-green-700 transition-colors">
Open in New Tab
</a>
<a href="/download/{{ result.video_path }}?t={{ result.timestamp }}" download 
class="px-6 py-3 bg-blue-600 text-white font-bold rounded-lg hover:bg-blue-700 transition-colors">
Download Video
</a>
</div>
{% endif %}
</div>
<!-- Right Column: Analysis Sidebar -->
<div class="lg:col-span-4 space-y-6">
<!-- Summary Card -->
<div class="bg-surface-container-lowest p-8 rounded-xl shadow-[0px_8px_24px_rgba(0,37,66,0.06)] relative overflow-hidden">
<div class="relative z-10">
<div class="flex items-center gap-3 mb-4">
<div class="bg-primary/5 p-2 rounded-lg text-primary">
<span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">analytics</span>
</div>
<h2 class="font-headline text-lg font-bold text-primary">Analysis Summary</h2>
</div>
<div class="space-y-1">
<p class="text-4xl font-headline font-extrabold text-primary tracking-tight">{% if result.stats %}{{ result.stats.count }}{% else %}0{% endif %} Vehicle{% if result.stats and result.stats.count != 1 %}s{% endif %} Detected</p>
<div class="flex items-center gap-2 text-on-tertiary-fixed-variant bg-tertiary-fixed/20 px-3 py-1 rounded-full w-fit">
<span class="material-symbols-outlined text-sm">check_circle</span>
<span class="text-xs font-semibold">Validation Successful</span>
</div>
</div>
</div>
<div class="absolute -bottom-8 -right-8 w-32 h-32 bg-primary/5 rounded-full blur-3xl"></div>
</div>
<!-- Breakdown Card -->
<div class="bg-surface-container-lowest rounded-xl shadow-[0px_8px_24px_rgba(0,37,66,0.06)] overflow-hidden">
<div class="px-6 py-4 border-b border-outline-variant/10 flex justify-between items-center">
<h3 class="font-headline text-sm font-bold text-on-surface uppercase tracking-wider">Classification Data</h3>
<span class="text-[10px] font-mono text-outline">v2.0.4</span>
</div>
<div class="p-0">
<table class="w-full text-left">
<thead>
<tr class="bg-surface-container-low">
<th class="px-6 py-3 text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">Class</th>
<th class="px-6 py-3 text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">Count</th>
<th class="px-6 py-3 text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">Avg Conf</th>
</tr>
</thead>
<tbody class="divide-y divide-outline-variant/10">
{% if result.stats and result.stats.breakdown %}
{% set class_icons = {'car': 'directions_car', 'motorcycle': 'two_wheeler', 'bus': 'directions_bus', 'truck': 'local_shipping'} %}
{% for class_name, count in result.stats.breakdown.items() %}
<tr class="hover:bg-surface-container-low transition-colors">
<td class="px-6 py-4 flex items-center gap-3">
<span class="material-symbols-outlined text-primary text-sm">{{ class_icons.get(class_name, 'directions_car') }}</span>
<span class="text-sm font-medium text-on-surface">{% if class_name == 'motorcycle' %}Motorcycle{% else %}{{ class_name|title }}{% endif %}</span>
</td>
<td class="px-6 py-4 text-sm font-mono text-on-surface">{{ "%02d"|format(count) }}</td>
<td class="px-6 py-4">
<div class="flex items-center gap-2">
<div class="w-12 h-1.5 bg-surface-container-high rounded-full overflow-hidden">
<div class="h-full bg-primary w-[95%]"></div>
</div>
<span class="text-xs font-mono font-bold text-primary">95%</span>
</div>
</td>
</tr>
{% endfor %}
{% else %}
<tr class="hover:bg-surface-container-low transition-colors">
<td class="px-6 py-4 flex items-center gap-3 opacity-40">
<span class="material-symbols-outlined text-sm">directions_car</span>
<span class="text-sm font-medium">Car</span>
</td>
<td class="px-6 py-4 text-sm font-mono opacity-40">00</td>
<td class="px-6 py-4 text-xs font-mono opacity-40">--</td>
</tr>
{% endif %}
</tbody>
</table>
</div>
</div>
<!-- Action Buttons -->
<div class="grid grid-cols-2 gap-4">
<button class="gradient-button text-white font-headline text-sm font-bold py-4 px-6 rounded-md shadow-lg active:scale-95 transition-all flex items-center justify-center gap-2" onclick="downloadPDF('{{ report_id }}')">
<span class="material-symbols-outlined text-lg">save</span>
                        Save Report
                    </button>
<button class="bg-surface-container-lowest text-primary font-headline text-sm font-bold py-4 px-6 rounded-md shadow-sm border border-outline-variant/20 hover:bg-surface-container-low active:scale-95 transition-all flex items-center justify-center gap-2" onclick="closeResultModal()">
<span class="material-symbols-outlined text-lg">refresh</span>
                        New Analysis
                    </button>
</div>
</div>
</div>
</main>
</div>
<script>
    // Show result modal when result is available
    {% if result %}
    document.addEventListener('DOMContentLoaded', function() {
        document.getElementById('resultModal').style.display = 'block';
    });
    {% endif %}

    async function downloadPDF(reportId) {
        console.log('[DEBUG] downloadPDF called with reportId:', reportId);
        if (!reportId || reportId === '') {
            alert('No report data found. Please run a new detection.');
            return;
        }
        
        // First save report to database
        let saveSuccess = false;
        try {
            const response = await fetch('/save_report/' + reportId, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            const result = await response.json();
            if (result.success) {
                console.log('[DEBUG] Report saved to database');
                saveSuccess = true;
            } else {
                console.warn('[WARN] Failed to save report:', result.error);
                alert('Failed to save report: ' + (result.error || 'Unknown error'));
            }
        } catch (err) {
            console.warn('[WARN] Error saving report:', err);
            alert('Error saving report: ' + err.message);
        }
        
        if (!saveSuccess) {
            return;  // Don't download PDF if save failed
        }
        
        // Then download PDF
        alert('Downloading PDF for report: ' + reportId);
        window.location.href = '/generate_pdf/' + reportId;
    }

    function closeResultModal() {
        document.getElementById('resultModal').style.display = 'none';
        window.location.href = '/';
    }
</script>
{% endif %}
</div>
</main>
<script>
        let pasteModeActive = false;
        const MAX_IMAGE_WIDTH = 1280;
        const MAX_IMAGE_HEIGHT = 720;
        const JPEG_QUALITY = 0.85;
        
        function compressImage(dataUrl, callback) {
            const img = new Image();
            img.onload = function() {
                let width = img.width;
                let height = img.height;
                
                if (width > MAX_IMAGE_WIDTH) {
                    height = Math.round(height * (MAX_IMAGE_WIDTH / width));
                    width = MAX_IMAGE_WIDTH;
                }
                if (height > MAX_IMAGE_HEIGHT) {
                    width = Math.round(width * (MAX_IMAGE_HEIGHT / height));
                    height = MAX_IMAGE_HEIGHT;
                }
                
                const canvas = document.createElement('canvas');
                canvas.width = width;
                canvas.height = height;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0, width, height);
                
                const compressedDataUrl = canvas.toDataURL('image/jpeg', JPEG_QUALITY);
                
                console.log('Original size: ' + Math.round(dataUrl.length / 1024) + 'KB');
                console.log('Compressed size: ' + Math.round(compressedDataUrl.length / 1024) + 'KB');
                
                callback(compressedDataUrl);
            };
            img.src = dataUrl;
        }
        
        async function enablePasteMode() {
            pasteModeActive = true;
            document.getElementById('copyPasteBtn').innerHTML = '<span class="material-symbols-outlined text-xl">hourglass_empty</span> Reading clipboard...';
            document.getElementById('copyPasteBtn').classList.add('bg-orange-100');
            document.getElementById('pasteInstructions').style.display = 'block';
            document.getElementById('pasteInstructions').textContent = 'Reading image from clipboard...';
            
            try {
                const clipboardItems = await navigator.clipboard.read();
                let imageFound = false;
                
                for (const item of clipboardItems) {
                    const imageType = item.types.find(type => type.startsWith('image/'));
                    
                    if (imageType) {
                        const blob = await item.getType(imageType);
                        const reader = new FileReader();
                        
                        reader.onload = function(event) {
                            const originalData = event.target.result;
                            
                            compressImage(originalData, function(compressedData) {
                                document.getElementById('pastedImageData').value = compressedData;
                                
                                const preview = document.getElementById('pastedPreview');
                                preview.src = compressedData;
                                document.getElementById('pastePreviewContainer').style.display = 'block';
                                
                                document.getElementById('fileInput').value = '';
                                
                                document.getElementById('copyPasteBtn').innerHTML = '<span class="material-symbols-outlined text-xl">check_circle</span> Image Pasted';
                                document.getElementById('copyPasteBtn').classList.remove('bg-orange-100');
                                document.getElementById('copyPasteBtn').classList.add('bg-green-100');
                                document.getElementById('pasteInstructions').textContent = 'Image auto-pasted! Click Detect Vehicles';
                                document.getElementById('pasteInstructions').style.color = '#4CAF50';
                            });
                        };
                        
                        reader.readAsDataURL(blob);
                        imageFound = true;
                        break;
                    }
                }
                
                if (!imageFound) {
                    document.getElementById('copyPasteBtn').innerHTML = '<span class="material-symbols-outlined text-xl">content_paste</span> Paste Mode Active';
                    document.getElementById('copyPasteBtn').classList.remove('bg-orange-100');
                    document.getElementById('copyPasteBtn').classList.add('bg-green-100');
                    document.getElementById('pasteInstructions').textContent = 'No image found. Press Ctrl+V to paste';
                    document.getElementById('pasteInstructions').style.color = '#f44336';
                    window.focus();
                }
                
            } catch (err) {
                console.error('Clipboard API error:', err);
                document.getElementById('copyPasteBtn').innerHTML = '<span class="material-symbols-outlined text-xl">content_paste</span> Paste Mode Active';
                document.getElementById('copyPasteBtn').classList.remove('bg-orange-100');
                document.getElementById('copyPasteBtn').classList.add('bg-green-100');
                document.getElementById('pasteInstructions').textContent = 'Please press Ctrl+V to paste your image';
                window.focus();
            }
        }
        
        function clearPastedImage() {
            document.getElementById('pastedImageData').value = '';
            document.getElementById('pastedPreview').src = '';
            document.getElementById('pastePreviewContainer').style.display = 'none';
            document.getElementById('fileInput').value = '';
            
            pasteModeActive = false;
            document.getElementById('copyPasteBtn').innerHTML = '<span class="material-symbols-outlined text-xl">content_paste</span> Paste Image';
            document.getElementById('copyPasteBtn').classList.remove('bg-green-100', 'bg-orange-100');
            document.getElementById('pasteInstructions').style.display = 'none';
        }
        
        document.addEventListener('paste', function(e) {
            const items = e.clipboardData.items;
            
            for (let i = 0; i < items.length; i++) {
                if (items[i].type.indexOf('image') !== -1) {
                    const blob = items[i].getAsFile();
                    const reader = new FileReader();
                    
                    reader.onload = function(event) {
                        const originalData = event.target.result;
                        
                        compressImage(originalData, function(compressedData) {
                            document.getElementById('pastedImageData').value = compressedData;
                            
                            const preview = document.getElementById('pastedPreview');
                            preview.src = compressedData;
                            document.getElementById('pastePreviewContainer').style.display = 'block';
                            
                            document.getElementById('fileInput').value = '';
                            
                            document.getElementById('copyPasteBtn').innerHTML = '<span class="material-symbols-outlined text-xl">check_circle</span> Image Pasted';
                            document.getElementById('copyPasteBtn').classList.add('bg-green-100');
                            document.getElementById('pasteInstructions').textContent = 'Image compressed and ready! Click "Detect Vehicles"';
                            document.getElementById('pasteInstructions').style.color = '#4CAF50';
                        });
                    };
                    
                    reader.readAsDataURL(blob);
                    break;
                }
            }
        });
        
        document.getElementById('uploadForm').addEventListener('submit', function(e) {
            const fileInput = document.getElementById('fileInput');
            const pastedData = document.getElementById('pastedImageData').value;
            
            if (!fileInput.value && !pastedData) {
                e.preventDefault();
                alert('Please either upload a file OR click "Paste Image" and paste an image (Ctrl+V)');
                return false;
            }
            
            document.getElementById('detectBtn').disabled = true;
            document.getElementById('detectBtn').innerHTML = '<span class="material-symbols-outlined animate-spin">refresh</span> Processing...';
            
            return true;
        });
        
        document.getElementById('fileInput').addEventListener('change', function() {
            if (this.value) {
                document.getElementById('pastedImageData').value = '';
                document.getElementById('pastePreviewContainer').style.display = 'none';
                const fileName = this.files[0] ? this.files[0].name : '';
                document.getElementById('fileName').textContent = fileName;
                document.getElementById('selectedFileDisplay').style.display = 'block';
            }
        });
        
        const dragDropArea = document.getElementById('dragDropArea');
        const dropZone = document.getElementById('uploadForm');
        const fileInput = document.getElementById('fileInput');
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
            document.body.addEventListener(eventName, preventDefaults, false);
        });
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, unhighlight, false);
        });
        
        function highlight(e) {
            dragDropArea.style.borderColor = '#4CAF50';
            dragDropArea.style.background = '#e8f5e9';
            dragDropArea.style.transform = 'scale(1.02)';
        }
        
        function unhighlight(e) {
            dragDropArea.style.borderColor = '';
            dragDropArea.style.background = '';
            dragDropArea.style.transform = 'scale(1)';
        }
        
        dropZone.addEventListener('drop', handleDrop, false);
        
        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            
            if (files.length > 0) {
                const file = files[0];
                const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'video/mp4', 'video/avi', 'video/quicktime'];
                
                if (validTypes.includes(file.type) || file.name.match(/\\.(jpg|jpeg|png|mp4|avi|mov)$/i)) {
                    const dataTransfer = new DataTransfer();
                    dataTransfer.items.add(file);
                    fileInput.files = dataTransfer.files;
                    
                    document.getElementById('fileName').textContent = file.name;
                    document.getElementById('selectedFileDisplay').style.display = 'block';
                    document.getElementById('pastedImageData').value = '';
                    document.getElementById('pastePreviewContainer').style.display = 'none';
                    
                    dragDropArea.innerHTML = `
                        <div class="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mb-6">
                            <span class="material-symbols-outlined text-green-600 text-4xl">check_circle</span>
                        </div>
                        <h2 class="text-xl font-bold text-green-600 mb-2">File Ready!</h2>
                        <p class="text-secondary max-w-sm">${file.name}</p>
                        <p class="text-sm text-slate-500 mt-2">Click "Detect Vehicles" to process</p>
                    `;
                } else {
                    alert('Invalid file type. Please upload: JPG, PNG, MP4, AVI, or MOV');
                }
            }
        }
        
        dragDropArea.addEventListener('click', function() {
            fileInput.click();
        });
        
        let webcamStream = null;
        let isWebcamRunning = false;
        
        async function startWebcam() {
            try {
                webcamStream = await navigator.mediaDevices.getUserMedia({ 
                    video: { width: 640, height: 480 } 
                });
                
                const webcamVideo = document.getElementById('webcamVideo');
                webcamVideo.srcObject = webcamStream;
                
                document.getElementById('webcamSection').style.display = 'block';
                document.getElementById('webcamInstructions').style.display = 'block';
                document.getElementById('webcamBtn').innerHTML = '<span class="material-symbols-outlined text-xl">videocam</span> Webcam Running';
                document.getElementById('webcamBtn').disabled = true;
                document.getElementById('webcamBtn').classList.add('opacity-50');
                
                document.getElementById('dragDropArea').parentElement.style.display = 'none';
                
                const detectionCanvas = document.getElementById('detectionCanvas');
                detectionCanvas.width = 640;
                detectionCanvas.height = 480;
                
                updateDetectionStatus('waiting', 'Initializing...');
                
                isWebcamRunning = true;
                
                processWebcamFrame();
                
                console.log('[INFO] Webcam started successfully');
                
            } catch (err) {
                console.error('[ERROR] Could not start webcam:', err);
                alert('Could not access webcam. Please make sure you have granted camera permissions.');
            }
        }
        
        function updateDetectionStatus(status, message) {
            const statusBadge = document.getElementById('detectionStatusBadge');
            const activityDiv = document.getElementById('detectionActivity');
            
            if (status === 'waiting') {
                statusBadge.textContent = 'Waiting...';
                statusBadge.style.background = '#FFC107';
                statusBadge.style.color = '#333';
                activityDiv.textContent = 'Initializing...';
                activityDiv.style.background = '#f5f5f5';
                activityDiv.style.color = '#666';
            } else if (status === 'processing') {
                statusBadge.textContent = 'Processing...';
                statusBadge.style.background = '#2196F3';
                statusBadge.style.color = 'white';
                activityDiv.textContent = 'Detecting...';
                activityDiv.style.background = '#e3f2fd';
                activityDiv.style.color = '#1976D2';
            } else if (status === 'detected') {
                statusBadge.textContent = 'DETECTED!';
                statusBadge.style.background = '#4CAF50';
                statusBadge.style.color = 'white';
                activityDiv.textContent = message;
                activityDiv.style.background = '#e8f5e9';
                activityDiv.style.color = '#2E7D32';
            } else if (status === 'none') {
                statusBadge.textContent = 'Scanning...';
                statusBadge.style.background = '#FF9800';
                statusBadge.style.color = 'white';
                activityDiv.textContent = 'No vehicles detected';
                activityDiv.style.background = '#fff3e0';
                activityDiv.style.color = '#E65100';
            }
        }
        
        async function processWebcamFrame() {
            if (!isWebcamRunning) return;
            
            const webcamVideo = document.getElementById('webcamVideo');
            const detectionCanvas = document.getElementById('detectionCanvas');
            const ctx = detectionCanvas.getContext('2d');
            
            ctx.drawImage(webcamVideo, 0, 0, 640, 480);
            
            const frameData = detectionCanvas.toDataURL('image/jpeg', 0.8);
            
            updateDetectionStatus('processing', 'Detecting...');
            
            try {
                const confThreshold = document.querySelector('input[name="confidence"]').value;
                const formData = new FormData();
                formData.append('image', frameData);
                formData.append('confidence', confThreshold);
                
                const response = await fetch('/webcam_detect', {
                    method: 'POST',
                    body: formData
                });
                
                if (response.ok) {
                    const result = await response.json();
                    
                    if (result.image) {
                        const img = new Image();
                        img.onload = function() {
                            ctx.drawImage(img, 0, 0, 640, 480);
                        };
                        img.src = 'data:image/jpeg;base64,' + result.image;
                        
                        document.getElementById('webcamStatsText').textContent = 
                            `Vehicles: ${result.count} | ${result.breakdown || 'No detections'}`;
                        
                        if (result.count > 0) {
                            updateDetectionStatus('detected', `${result.count} vehicle(s) detected: ${result.breakdown}`);
                        } else {
                            updateDetectionStatus('none', 'No vehicles detected');
                        }
                    }
                } else {
                    console.error('[ERROR] Detection failed:', response.status);
                    updateDetectionStatus('none', 'Detection error');
                }
            } catch (err) {
                console.error('[ERROR] Frame processing error:', err);
                updateDetectionStatus('none', 'Processing error');
            }
            
            if (isWebcamRunning) {
                setTimeout(processWebcamFrame, 100);
            }
        }
        
        function stopWebcam() {
            isWebcamRunning = false;
            
            if (webcamStream) {
                webcamStream.getTracks().forEach(track => track.stop());
                webcamStream = null;
            }
            
            document.getElementById('webcamSection').style.display = 'none';
            document.getElementById('webcamInstructions').style.display = 'none';
            
            document.getElementById('webcamBtn').innerHTML = '<span class="material-symbols-outlined text-xl">videocam</span> Live Webcam';
            document.getElementById('webcamBtn').disabled = false;
            document.getElementById('webcamBtn').classList.remove('opacity-50');
            
            document.getElementById('dragDropArea').parentElement.style.display = 'block';
            
            const detectionCanvas = document.getElementById('detectionCanvas');
            const ctx = detectionCanvas.getContext('2d');
            ctx.clearRect(0, 0, detectionCanvas.width, detectionCanvas.height);
            
            console.log('[INFO] Webcam stopped');
        }
        
        // Force demo video to play
        document.addEventListener('DOMContentLoaded', function() {
            const demoVideo = document.getElementById('demoVideo');
            if (demoVideo) {
                demoVideo.play().then(function() {
                    console.log('[INFO] Demo video playing successfully');
                }).catch(function(error) {
                    console.log('[WARN] Autoplay blocked:', error);
                    // Try to play on first interaction
                    document.body.addEventListener('click', function() {
                        demoVideo.play();
                    }, { once: true });
                });
            }
        });
    </script>
</body>
</html>
"""


def detect_vehicles_image(image_data, conf_threshold=0.4):
    """Process image and detect vehicles"""
    start_time = time.time()
    
    # Decode image
    nparr = np.frombuffer(image_data, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if image is None:
        return None, "Error: Could not decode image"
    
    height, width = image.shape[:2]
    print(f"\n{'='*60}")
    print("IMAGE PROCESSING STARTED")
    print(f"{'='*60}")
    print(f"Resolution: {width}x{height}")
    print(f"Confidence Threshold: {conf_threshold}")
    print(f"{'='*60}\n")
    
    # Run detection
    results = model.predict(
        image,
        imgsz=320,  # Reduced for faster Pi performance
        conf=conf_threshold,
        verbose=False,
        classes=list(VEHICLE_CLASSES.keys())
    )
    
    # Process detections
    detections = []
    class_counts = {}
    annotated = image.copy()
    
    for result in results:
        boxes = result.boxes
        if boxes is None:
            continue
        
        for box in boxes:
            class_id = int(box.cls.item())
            conf = float(box.conf.item())
            
            if class_id in VEHICLE_CLASSES:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                class_name = VEHICLE_CLASSES[class_id]
                
                detections.append({'class': class_name, 'conf': conf})
                class_counts[class_name] = class_counts.get(class_name, 0) + 1
                
                # Draw box
                color = CLASS_COLORS[class_name]
                cv2.rectangle(annotated, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                
                # Draw label
                # Use display name (Motorcycle/Scooty instead of just motorcycle)
                display_name = DISPLAY_NAMES.get(class_name, class_name)
                label = f"{display_name}: {conf:.2f}"
                (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
                cv2.rectangle(annotated, (int(x1), int(y1) - label_h - 10),
                            (int(x1) + label_w, int(y1)), color, -1)
                cv2.putText(annotated, label, (int(x1), int(y1) - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
    
    # Add stats
    processing_time = time.time() - start_time
    cv2.rectangle(annotated, (0, 0), (300, 80), (0, 0, 0), -1)
    cv2.putText(annotated, f"Vehicles: {len(detections)}", (10, 30),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(annotated, f"Time: {processing_time:.3f}s", (10, 60),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    # Print summary to terminal
    print(f"\n{'='*60}")
    print("IMAGE PROCESSING COMPLETE")
    print(f"{'='*60}")
    print(f"Total Vehicles Detected: {len(detections)}")
    print(f"Processing Time: {processing_time:.3f}s")
    if class_counts:
        print(f"Breakdown:")
        for cls, count in class_counts.items():
            display_name = DISPLAY_NAMES.get(cls, cls)
            print(f"  - {display_name}: {count}")
    print(f"{'='*60}\n")
    
    # Encode to base64
    _, buffer = cv2.imencode('.jpg', annotated)
    img_base64 = base64.b64encode(buffer).decode('utf-8')
    
    # Prepare message
    if len(detections) > 0:
        message = f"SUCCESS: Detected {len(detections)} vehicle(s)"
    else:
        message = "NO VEHICLES DETECTED"
    
    return img_base64, message, {
        'time': f"{processing_time:.3f}s",
        'count': len(detections),
        'breakdown': class_counts
    }


def extract_video_first_frame(video_path):
    """Extract first frame from video as base64 image for preview"""
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None
        ret, frame = cap.read()
        cap.release()
        if ret and frame is not None:
            # Resize to reasonable size for preview
            height, width = frame.shape[:2]
            max_width = 640
            if width > max_width:
                ratio = max_width / width
                new_height = int(height * ratio)
                frame = cv2.resize(frame, (max_width, new_height))
            # Convert to RGB and encode
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            _, buffer = cv2.imencode('.jpg', frame_rgb)
            return base64.b64encode(buffer).decode('utf-8')
    except Exception as e:
        print(f"[WARN] Could not extract first frame: {e}")
    return None


def detect_vehicles_video(video_path, output_path, conf_threshold=0.4):
    """Process video and detect vehicles with terminal progress output"""
    start_time = time.time()
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("[ERROR] Could not open video file")
        return None, "Error: Could not open video", None
    
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"\n{'='*60}")
    print("VIDEO PROCESSING STARTED")
    print(f"{'='*60}")
    print(f"Resolution: {frame_width}x{frame_height}")
    print(f"FPS: {fps:.1f}")
    print(f"Total Frames: {total_frames}")
    print(f"Confidence Threshold: {conf_threshold}")
    print(f"{'='*60}\n")
    
    # Try multiple codecs in order of browser compatibility
    # H264 is required for browser playback, mp4v only works in desktop players
    codecs_to_try = [
        ('avc1', 'H264'),  # Most compatible with browsers
        ('H264', 'H264'),  # Alternative H264 identifier
        ('X264', 'X264'),  # Another H264 variant
        ('h264', 'H264'),  # Lowercase variant
        ('MP4V', 'MPEG-4'),  # Less compatible but common
        ('mp4v', 'MPEG-4'),  # Lowercase variant
    ]
    
    writer = None
    used_codec = None
    
    for fourcc_code, codec_name in codecs_to_try:
        try:
            fourcc = cv2.VideoWriter_fourcc(*fourcc_code)
            writer = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))
            if writer.isOpened():
                used_codec = codec_name
                print(f"[INFO] Successfully using {codec_name} codec ({fourcc_code})")
                break
            else:
                writer.release()
                writer = None
        except Exception as e:
            print(f"[DEBUG] Codec {fourcc_code} failed: {e}")
            continue
    
    if writer is None or not writer.isOpened():
        print("[ERROR] Could not open video writer with any codec")
        return None, "Error: Could not create output video - no compatible codec found"
    
    total_detections = 0
    frame_count = 0
    class_counts = {}
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Run detection
            try:
                results = model.predict(
                    frame,
                    imgsz=480,
                    conf=conf_threshold,
                    verbose=False,
                    classes=list(VEHICLE_CLASSES.keys())
                )
            except Exception as e:
                print(f"[ERROR] Detection failed on frame {frame_count}: {e}")
                # Write original frame without detection if detection fails
                writer.write(frame)
                frame_count += 1
                continue
            
            annotated = frame.copy()
            frame_detections = 0
            
            for result in results:
                boxes = result.boxes
                if boxes is None:
                    continue
                
                for box in boxes:
                    class_id = int(box.cls.item())
                    conf = float(box.conf.item())
                    
                    if class_id in VEHICLE_CLASSES:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        class_name = VEHICLE_CLASSES[class_id]
                        
                        frame_detections += 1
                        total_detections += 1
                        class_counts[class_name] = class_counts.get(class_name, 0) + 1
                        
                        color = CLASS_COLORS[class_name]
                        cv2.rectangle(annotated, (int(x1), int(y1)), 
                                    (int(x2), int(y2)), color, 2)
                        
                        # Use display name (Motorcycle/Scooty instead of just motorcycle)
                        display_name = DISPLAY_NAMES.get(class_name, class_name)
                        label = f"{display_name}: {conf:.2f}"
                        (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
                        cv2.rectangle(annotated, (int(x1), int(y1) - label_h - 10),
                                    (int(x1) + label_w, int(y1)), color, -1)
                        cv2.putText(annotated, label, (int(x1), int(y1) - 5),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
            
            # Add frame info
            cv2.putText(annotated, f"Frame: {frame_count}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            writer.write(annotated)
            frame_count += 1
            
            # Print progress every 30 frames
            if frame_count % 30 == 0 or frame_count == 1:
                elapsed = time.time() - start_time
                progress_pct = (frame_count / total_frames * 100) if total_frames > 0 else 0
                current_fps = frame_count / elapsed if elapsed > 0 else 0
                print(f"[PROGRESS] Frame {frame_count}/{total_frames} ({progress_pct:.1f}%) | "
                      f"Vehicles: {total_detections} | FPS: {current_fps:.1f}")
    
    finally:
        cap.release()
        if writer:
            writer.release()
        # Ensure file is fully written and closed
        time.sleep(0.2)
        
        # Verify video was created and has content
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"[INFO] Output video file size: {file_size / 1024 / 1024:.2f} MB")
            if file_size == 0:
                print("[ERROR] Video file is empty!")
            elif used_codec and 'H264' not in used_codec:
                # Try to convert to H264 using ffmpeg if available
                print("[INFO] Attempting to convert video to H264 for browser compatibility...")
                try:
                    import subprocess
                    temp_converted = output_path.replace('.mp4', '_h264.mp4')
                    result = subprocess.run([
                        'ffmpeg', '-y', '-i', output_path,
                        '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
                        '-c:a', 'aac', '-movflags', '+faststart',
                        temp_converted
                    ], capture_output=True, text=True, timeout=60)
                    
                    if result.returncode == 0 and os.path.exists(temp_converted):
                        # Replace original with converted
                        os.replace(temp_converted, output_path)
                        used_codec = 'H264 (ffmpeg converted)'
                        print("[SUCCESS] Video converted to H264 for browser playback")
                    else:
                        print(f"[WARN] ffmpeg conversion failed: {result.stderr[:200]}")
                        if os.path.exists(temp_converted):
                            os.remove(temp_converted)
                except FileNotFoundError:
                    print("[INFO] ffmpeg not found - install ffmpeg for better browser compatibility")
                except Exception as e:
                    print(f"[WARN] ffmpeg conversion error: {e}")
        else:
            print("[ERROR] Video file was not created!")
    
    processing_time = time.time() - start_time
    avg_fps = frame_count / processing_time if processing_time > 0 else 0
    
    # Print final summary
    print(f"\n{'='*60}")
    print("VIDEO PROCESSING COMPLETE")
    print(f"{'='*60}")
    print(f"Total Frames Processed: {frame_count}")
    print(f"Total Vehicles Detected: {total_detections}")
    print(f"Processing Time: {processing_time:.1f}s")
    print(f"Average FPS: {avg_fps:.1f}")
    if class_counts:
        print(f"Breakdown:")
        for cls, count in class_counts.items():
            display_name = DISPLAY_NAMES.get(cls, cls)
            print(f"  - {display_name}: {count}")
    print(f"{'='*60}\n")
    
    # Add codec info to message
    codec_info = f" (Codec: {used_codec})" if used_codec else " (Codec: unknown)"
    
    if total_detections > 0:
        message = f"SUCCESS: Processed {frame_count} frames, detected {total_detections} vehicles{codec_info}"
    else:
        message = f"NO VEHICLES: Processed {frame_count} frames, no vehicles detected{codec_info}"
    
    # Extract first frame for preview
    first_frame = extract_video_first_frame(output_path)
    
    return output_path, message, {
        'time': f"{processing_time:.1f}s ({avg_fps:.1f} FPS)",
        'count': total_detections,
        'breakdown': class_counts,
        'codec': used_codec if used_codec else 'unknown',
        'first_frame': first_frame
    }


@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    result = None
    conf_threshold = 0.5
    
    if request.method == 'POST':
        # Get confidence threshold
        conf_threshold = float(request.form.get('confidence', 0.4))
        
        # Check for pasted image first
        pasted_image_data = request.form.get('pasted_image', '')
        
        pasted_image_processed = False
        
        if pasted_image_data and pasted_image_data.startswith('data:image'):
            # Handle pasted image from clipboard
            try:
                # Extract base64 data from data URL
                # Format: data:image/png;base64,xxxxxx
                base64_data = pasted_image_data.split(',')[1]
                file_data = base64.b64decode(base64_data)
                
                # Process as image
                img_base64, message, stats = detect_vehicles_image(file_data, conf_threshold)
                
                result = {
                    'success': stats['count'] > 0,
                    'message': message,
                    'image': img_base64,
                    'stats': stats
                }
                
                # Set flag to skip regular file upload handling
                pasted_image_processed = True
            except Exception as e:
                flash(f'Error processing pasted image: {str(e)}')
                return redirect(request.url)
        
        # Handle regular file upload (only if not already processed)
        if not pasted_image_processed:
            if 'file' not in request.files:
                flash('No file uploaded')
                return redirect(request.url)
            
            file = request.files['file']
            if file.filename == '':
                flash('No file selected')
                return redirect(request.url)
            
            # Read file data
            file_data = file.read()
            filename = file.filename.lower()
            
            if filename.endswith(('.jpg', '.jpeg', '.png')):
                # Process image
                img_base64, message, stats = detect_vehicles_image(file_data, conf_threshold)
                
                result = {
                    'success': stats['count'] > 0,
                    'message': message,
                    'image': img_base64,
                    'stats': stats
                }
                
            elif filename.endswith(('.mp4', '.avi', '.mov')):
                # Process video
                # Save uploaded video temporarily
                temp_input = tempfile.mktemp(suffix='.mp4')
                with open(temp_input, 'wb') as f:
                    f.write(file_data)
                
                # Create output path in static directory for reliable serving
                timestamp = int(time.time())
                temp_output = os.path.join(STATIC_DIR, f'processed_{timestamp}.mp4')
                
                video_path, message, stats = detect_vehicles_video(temp_input, temp_output, conf_threshold)
                
                # Clean up input
                os.remove(temp_input)
                
                # Use relative path from static folder
                video_filename = os.path.basename(temp_output)
                
                result = {
                    'success': stats['count'] > 0,
                    'message': message,
                    'video_path': video_filename,
                    'timestamp': timestamp,
                    'stats': stats
                }
                
                # Store output path for cleanup later
                if not hasattr(app, 'temp_videos'):
                    app.temp_videos = {}
                app.temp_videos[video_filename] = temp_output
                
            else:
                flash('Unsupported file format. Use: JPG, PNG, MP4, AVI, MOV')
                return redirect(request.url)
    
    # Store result for PDF generation and history
    report_id = ''
    if result:
        report_id = str(uuid.uuid4())[:8]

        print(f"[DEBUG] Result stats: {result.get('stats')}, type: {type(result.get('stats'))}")

        # Get user info from session and database
        user_id = session.get('user_id')
        username = session.get('username')
        user_info_for_pdf = None
        
        if user_id:
            try:
                db = get_db()
                if db:
                    user = db.query(User).filter(User.id == user_id).first()
                    if user:
                        user_info_for_pdf = {
                            'id': user.id,
                            'username': user.username,
                            'email': user.email
                        }
                    db.close()
            except Exception as e:
                print(f"[WARN] Could not fetch user info: {e}")
        
        print(f"[DEBUG] Storing result for user_id: {user_id}, username: {username}, user_info: {user_info_for_pdf}")

        app.stored_results[report_id] = {
            'stats': result.get('stats', {}),
            'message': result.get('message', ''),
            'image': result.get('image', ''),
            'video_path': result.get('video_path', ''),
            'conf_threshold': conf_threshold if request.method == 'POST' else 0.5,
            'input_type': 'video' if result.get('video_path') else 'image',
            'user_id': user_id,
            'user_info': user_info_for_pdf  # Store full user info for PDF
        }
        print(f"[DEBUG] Result stored with report_id: {report_id} for user_id: {user_id}")
        # Note: Data is saved to database only when user clicks 'Save Report' button

    return render_template_string(HTML_TEMPLATE, result=result, report_id=report_id)


@app.route('/debug')
def debug_status():
    """Debug route to check database and session status"""
    user_id = session.get('user_id')
    username = session.get('username')
    
    db_status = "Not connected"
    table_count = 0
    
    db = get_db()
    if db:
        try:
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            db_status = f"Connected ({engine.url.drivername})"
            table_count = len(tables)
            db.close()
        except Exception as e:
            db_status = f"Error: {str(e)}"
    
    return {
        'session_user_id': user_id,
        'session_username': username,
        'database_status': db_status,
        'tables': table_count,
        'stored_results_count': len(app.stored_results)
    }


@app.route('/generate_pdf/<report_id>')
def generate_pdf(report_id):
    """Generate and download PDF report for a detection result"""
    print(f"[DEBUG] PDF route called with report_id: {report_id}")
    print(f"[DEBUG] Stored results keys: {list(app.stored_results.keys())}")
    
    # Get user_id from session first
    user_id = session.get('user_id')
    print(f"[DEBUG] PDF Generation - Session user_id: {user_id}")
    
    # Try to get data from stored results first
    data = None
    if report_id in app.stored_results:
        data = app.stored_results[report_id]
        print(f"[DEBUG] Data found in stored_results")
    else:
        # If not in stored results, fetch from database
        print(f"[DEBUG] Report ID not in stored results, fetching from database")
        db = get_db()
        if db:
            try:
                # Fetch from detection_history table
                record = db.query(DetectionHistory).filter(
                    DetectionHistory.report_id == report_id
                ).first()
                
                if record:
                    # Verify user_id matches if user is logged in
                    if user_id and record.user_id != user_id:
                        print(f"[WARN] User {user_id} trying to access report belonging to user {record.user_id}")
                        return "Access denied. This report belongs to another user.", 403
                    
                    data = {
                        'stats': {'count': record.vehicle_count, 'time': record.processing_time},
                        'conf_threshold': record.confidence_threshold or 0.5,
                        'input_type': record.detection_type,
                        'image': record.image_data or '',
                        'breakdown': record.breakdown or '',
                        'video_path': record.video_path or '',
                        'user_id': record.user_id
                    }
                    print(f"[DEBUG] Data fetched from database for report_id: {report_id}")
                else:
                    print(f"[DEBUG] Report ID not found in database")
                    return "Report not found. Please run a new detection.", 404
            except Exception as e:
                print(f"[ERROR] Failed to fetch report from database: {e}")
                import traceback
                traceback.print_exc()
                return "Error fetching report data.", 500
            finally:
                db.close()
        else:
            return "Report not found. Please run a new detection.", 404
    
    if not data:
        return "Report not found. Please run a new detection.", 404
    
    stats = data.get('stats', {})
    vehicle_count = stats.get('count', 0)
    processing_time = stats.get('time', '--')
    breakdown = stats.get('breakdown', {})
    conf_threshold = data.get('conf_threshold', 0.5)
    input_type = data.get('input_type', 'image')
    img_base64 = data.get('image', '')
    video_path = data.get('video_path', '')
    first_frame = stats.get('first_frame', '') if isinstance(stats, dict) else ''

    # Extract video frames if video exists
    video_frames = []
    if video_path:
        video_frames = extract_frames_from_video(video_path)

    # Get user information from stored data (saved at detection time)
    user_info = data.get('user_info')
    print(f"[DEBUG] user_info from stored_results: {user_info}")
    print(f"[DEBUG] Full data keys: {list(data.keys())}")
    
    # If not in stored data, try to fetch using user_id from stored data
    if not user_info:
        stored_user_id = data.get('user_id')
        print(f"[DEBUG] user_info not in stored data, trying stored_user_id: {stored_user_id}")
        if stored_user_id:
            try:
                db = get_db()
                if db:
                    user = db.query(User).filter(User.id == stored_user_id).first()
                    if user:
                        user_info = {
                            'id': user.id,
                            'username': user.username,
                            'email': user.email
                        }
                        print(f"[DEBUG] Fetched user from DB using stored_user_id: {user_info}")
                    db.close()
            except Exception as e:
                print(f"[ERROR] DB query failed: {e}")
    
    if not user_info:
        print(f"[WARN] No user info available, PDF will show Guest")

    try:
        pdf = FPDF('P', 'mm', 'A4')
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # ---- Header Bar ----
        pdf.set_fill_color(0, 37, 66)
        pdf.rect(0, 0, 210, 40, 'F')  # Increased height to 40mm
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 22)
        pdf.set_xy(15, 12)
        pdf.cell(0, 10, 'Vehicle Detection Report', ln=True)
        pdf.set_font('Helvetica', '', 10)
        pdf.set_xy(15, 24)
        pdf.cell(0, 6, 'Generated: ' + time.strftime('%Y-%m-%d %H:%M:%S'), ln=True)
        
        # ---- User Info (Right side of header) ----
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_xy(130, 12)
        if user_info:
            pdf.cell(0, 6, f"User: {user_info['username']}", ln=True)
        else:
            pdf.cell(0, 6, "User: Guest", ln=True)
        
        pdf.set_font('Helvetica', '', 10)
        pdf.set_xy(130, 20)
        if user_info:
            pdf.cell(0, 6, f"ID: {user_info['id']}", ln=True)
        else:
            pdf.cell(0, 6, "ID: N/A", ln=True)

        y = 42

        # ---- Summary Card ----
        pdf.set_fill_color(238, 237, 240)
        pdf.rect(15, y, 180, 26, 'F')
        pdf.set_text_color(0, 37, 66)
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_xy(20, y + 4)
        count_text = f"{vehicle_count} Vehicle{'s' if vehicle_count != 1 else ''} Detected"
        pdf.cell(0, 8, count_text, ln=True)
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(80, 80, 80)
        pdf.set_xy(20, y + 14)
        pdf.cell(0, 6, f"Processing Time: {processing_time}  |  Model: YOLOv8  |  Confidence: {conf_threshold}  |  Input: {input_type}", ln=True)
        y += 32

        # ---- Detection Image ----
        image_data = img_base64 if img_base64 else first_frame
        if image_data:
            try:
                # Strip data URL prefix if present
                if image_data.startswith('data:image/'):
                    image_data = image_data.split(',')[1]
                img_bytes = base64.b64decode(image_data)
                img_path = os.path.join(STATIC_DIR, f'temp_pdf_img_{report_id}.jpg')
                with open(img_path, 'wb') as f:
                    f.write(img_bytes)
                pdf.image(img_path, x=15, y=y, w=180, h=85)
                y += 90
                # Clean up temp image
                try:
                    os.remove(img_path)
                except:
                    pass
            except Exception as img_err:
                print(f"[WARN] Could not add image to PDF: {img_err}")
                y += 5

        # ---- Video Frames (if available) ----
        if video_frames:
            pdf.set_text_color(0, 37, 66)
            pdf.set_font('Helvetica', 'B', 13)
            pdf.set_xy(15, y)
            pdf.cell(0, 8, 'Video Detection Frames', ln=True)
            y += 10
            
            # Add up to 3 video frames
            for i, frame_bytes in enumerate(video_frames[:3]):
                try:
                    frame_path = os.path.join(STATIC_DIR, f'temp_pdf_frame_{report_id}_{i}.jpg')
                    with open(frame_path, 'wb') as f:
                        f.write(frame_bytes)
                    pdf.image(frame_path, x=15, y=y, w=85, h=60)
                    # Clean up temp frame
                    try:
                        os.remove(frame_path)
                    except:
                        pass
                    
                    # Add second frame on same row if available
                    if i + 1 < len(video_frames[:3]):
                        next_frame_bytes = video_frames[i + 1]
                        next_frame_path = os.path.join(STATIC_DIR, f'temp_pdf_frame_{report_id}_{i+1}.jpg')
                        with open(next_frame_path, 'wb') as f:
                            f.write(next_frame_bytes)
                        pdf.image(next_frame_path, x=110, y=y, w=85, h=60)
                        try:
                            os.remove(next_frame_path)
                        except:
                            pass
                        i += 1  # Skip next frame since we already added it
                    
                    y += 65
                except Exception as frame_err:
                    print(f"[WARN] Could not add video frame {i} to PDF: {frame_err}")
            
            y += 5

        # ---- Classification Table ----
        pdf.set_text_color(0, 37, 66)
        pdf.set_font('Helvetica', 'B', 13)
        pdf.set_xy(15, y)
        pdf.cell(0, 8, 'Classification Breakdown', ln=True)
        y += 10

        # Table header
        pdf.set_fill_color(0, 37, 66)
        pdf.rect(15, y, 180, 9, 'F')
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_xy(20, y + 2)
        pdf.cell(60, 6, 'Vehicle Class', border=0)
        pdf.cell(30, 6, 'Count', border=0)
        pdf.cell(40, 6, 'Avg Confidence', border=0)
        y += 9

        # Table rows
        class_display = {'car': 'Car', 'motorcycle': 'Motorcycle/Scooty', 'bus': 'Bus', 'truck': 'Truck'}
        row_idx = 0
        if breakdown:
            for cls_name, count in breakdown.items():
                if row_idx % 2 == 0:
                    pdf.set_fill_color(245, 243, 246)
                else:
                    pdf.set_fill_color(255, 255, 255)
                pdf.rect(15, y, 180, 9, 'F')
                pdf.set_text_color(30, 30, 30)
                pdf.set_font('Helvetica', '', 10)
                pdf.set_xy(20, y + 2)
                display = class_display.get(cls_name, cls_name.title())
                pdf.cell(60, 6, display, border=0)
                pdf.set_font('Helvetica', 'B', 10)
                pdf.cell(30, 6, str(count), border=0)
                pdf.set_font('Helvetica', '', 10)
                pdf.cell(40, 6, '> 85%', border=0)
                y += 9
                row_idx += 1
        else:
            pdf.set_fill_color(245, 243, 246)
            pdf.rect(15, y, 180, 9, 'F')
            pdf.set_text_color(150, 150, 150)
            pdf.set_font('Helvetica', '', 10)
            pdf.set_xy(20, y + 2)
            pdf.cell(0, 6, 'No vehicles detected', border=0)
            y += 9

        # Table border
        pdf.set_draw_color(200, 200, 200)
        pdf.set_line_width(0.3)
        table_rows = max(row_idx, 1) + 1
        pdf.rect(15, y - 9 * table_rows, 180, 9 * table_rows)

        # ---- Footer ----
        pdf.set_text_color(170, 170, 170)
        pdf.set_font('Helvetica', '', 8)
        pdf.set_xy(0, 285)
        pdf.cell(210, 5, 'Vehicle Detection System - Powered by YOLOv8', align='C')

        # ---- Save to buffer and send ----
        pdf_buffer = BytesIO()
        pdf.output(pdf_buffer)
        pdf_buffer.seek(0)

        # Include user_id in filename if available
        user_id_for_filename = data.get('user_id', 'guest')
        if user_info and user_info.get('id'):
            user_id_for_filename = user_info['id']
        filename = f"Vehicle_Detection_Report_User{user_id_for_filename}_{time.strftime('%Y%m%d_%H%M%S')}.pdf"
        print(f"[INFO] PDF generated: {filename}")

        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        print(f"[ERROR] PDF generation failed: {e}")
        import traceback
        traceback.print_exc()
        return "Error generating PDF", 500


@app.route('/view_report/<report_id>')
@login_required
def view_report(report_id):
    """View report in browser instead of downloading"""
    print(f"[DEBUG] view_report called with report_id: {report_id}")
    
    user_id = session.get('user_id')
    
    # Fetch from database
    db = get_db()
    if not db:
        return "Database connection error", 500
    
    try:
        record = db.query(DetectionHistory).filter(
            DetectionHistory.report_id == report_id
        ).first()
        
        if not record:
            return "Report not found", 404
        
        # Verify user ownership
        if record.user_id != user_id:
            return "Access denied", 403
        
        # Parse breakdown if it's a string
        breakdown_dict = {}
        if record.breakdown:
            try:
                if isinstance(record.breakdown, str):
                    import ast
                    breakdown_dict = ast.literal_eval(record.breakdown)
                elif isinstance(record.breakdown, dict):
                    breakdown_dict = record.breakdown
            except:
                breakdown_dict = {}
        
        # Prepare data for view
        report_data = {
            'report_id': report_id,
            'timestamp': record.timestamp,
            'detection_type': record.detection_type,
            'vehicle_count': record.vehicle_count,
            'breakdown': breakdown_dict,
            'image_data': record.image_data,
            'video_path': record.video_path,
            'processing_time': record.processing_time or '--',
            'confidence_threshold': record.confidence_threshold or 0.5
        }
        
        return render_template_string(VIEW_REPORT_TEMPLATE, report=report_data)
    except Exception as e:
        print(f"[ERROR] Error in view_report: {e}")
        import traceback
        traceback.print_exc()
        return "Error loading report", 500
    finally:
        db.close()


@app.route('/delete_detection/<report_id>', methods=['DELETE'])
@login_required
def delete_detection(report_id):
    """Delete a detection record from the database"""
    db = None
    try:
        user_id = session.get('user_id')
        print(f"[DEBUG] Delete detection - report_id: {report_id}, user_id: {user_id}")
        
        db = get_db()
        if not db:
            return {'success': False, 'error': 'Database connection failed'}, 500
        
        # Find the record
        record = db.query(DetectionHistory).filter(
            DetectionHistory.report_id == report_id
        ).first()
        
        if not record:
            return {'success': False, 'error': 'Record not found'}, 404
        
        # Verify user ownership
        if record.user_id != user_id:
            print(f"[WARN] User {user_id} trying to delete record belonging to user {record.user_id}")
            return {'success': False, 'error': 'Access denied'}, 403
        
        # Delete video file if exists
        if record.video_path:
            video_full_path = os.path.join(STATIC_DIR, record.video_path)
            if os.path.exists(video_full_path):
                try:
                    os.remove(video_full_path)
                    print(f"[INFO] Deleted video file: {video_full_path}")
                except Exception as e:
                    print(f"[WARN] Could not delete video file: {e}")
        
        # Delete the record
        db.delete(record)
        db.commit()
        print(f"[INFO] Deleted detection record: {report_id}")
        
        return {'success': True}
    except Exception as e:
        print(f"[ERROR] Failed to delete detection: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}, 500
    finally:
        if db:
            db.close()


@app.route('/save_report/<report_id>', methods=['POST'])
@login_required
def save_report(report_id):
    """Save detection report to database when user clicks Save Report"""
    print(f"[DEBUG] save_report called for report_id: {report_id}")
    
    if report_id not in app.stored_results:
        return {'success': False, 'error': 'Report not found'}, 404
    
    data = app.stored_results[report_id]
    stats = data.get('stats', {})
    input_type = data.get('input_type', 'image')
    
    # Get user_id from session
    user_id = session.get('user_id')
    stored_user_id = data.get('user_id')
    print(f"[DEBUG] Session user_id: {user_id}, Stored result user_id: {stored_user_id}, Session data: {dict(session)}")
    
    # Verify user owns this report
    if stored_user_id and stored_user_id != user_id:
        print(f"[WARN] User mismatch! Session: {user_id}, Report owner: {stored_user_id}")
        return {'success': False, 'error': 'Access denied - report belongs to another user'}, 403
    
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    message = data.get('message', '')
    image_data = data.get('image', '')
    video_path = data.get('video_path', '')
    conf_threshold = data.get('conf_threshold', 0.5)
    
    # Save to database
    try:
        success = save_detection_to_db(
            report_id=report_id,
            timestamp=timestamp,
            input_type=input_type,
            message=message,
            stats=stats,
            image_data=image_data,
            video_path=video_path,
            conf_threshold=conf_threshold
        )
        
        if success:
            print(f"[INFO] Report {report_id} saved to database by user {user_id}")
            return {'success': True, 'message': 'Report saved successfully'}
        else:
            print(f"[ERROR] save_detection_to_db returned False for report {report_id}")
            return {'success': False, 'error': 'Failed to save to database'}, 500
    except Exception as e:
        print(f"[ERROR] Exception in save_report: {e}")
        import traceback
        traceback.print_exc()
        error_msg = str(e)
        # Check for common database errors
        if 'foreign key' in error_msg.lower():
            error_msg = "User authentication error - please log in again"
        elif 'unique' in error_msg.lower():
            error_msg = "Report already exists"
        return {'success': False, 'error': f'Failed to save to database: {error_msg}'}, 500


@app.route('/download/<path:filename>')
def download(filename):
    if hasattr(app, 'temp_videos') and filename in app.temp_videos:
        return send_file(app.temp_videos[filename], as_attachment=True)
    return "File not found", 404


@app.route('/webcam_detect', methods=['POST'])
def webcam_detect():
    """Process webcam frame for live detection with vehicle counting"""
    try:
        print(f"[DEBUG] webcam_detect called")
        print(f"[DEBUG] Request form keys: {list(request.form.keys())}")
        print(f"[DEBUG] Request files keys: {list(request.files.keys())}")
        
        # Get image data from request (FormData)
        image_data = request.form.get('image')
        conf_threshold = float(request.form.get('confidence', 0.4))
        
        # Get counting line position (default: middle of frame)
        count_line_y = float(request.form.get('count_line_y', 0.5))
        
        print(f"[DEBUG] Image data length: {len(image_data) if image_data else 0}")
        print(f"[DEBUG] Confidence threshold: {conf_threshold}")
        print(f"[DEBUG] Count line Y: {count_line_y}")

        if not image_data:
            print(f"[ERROR] No image data provided")
            return {'error': 'No image data provided'}, 400

        # Decode base64 image
        import base64
        # Remove data URL prefix if present
        if 'base64,' in image_data:
            image_data = image_data.split('base64,')[1]
        
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            return {'error': 'Could not decode image'}, 400

        # Calculate counting line Y position
        frame_height = image.shape[0]
        count_line_pixel = int(frame_height * count_line_y)

        # Run detection - smaller imgsz for faster inference on Pi
        results = model.predict(
            image,
            imgsz=320,  # Reduced from 640 for faster Pi performance
            conf=conf_threshold,
            verbose=False,
            classes=list(VEHICLE_CLASSES.keys())
        )

        # Process detections for tracker
        detections = []
        class_counts = {}
        annotated = image.copy()

        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue

            for box in boxes:
                class_id = int(box.cls.item())
                conf = float(box.conf.item())

                if class_id in VEHICLE_CLASSES:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    class_name = VEHICLE_CLASSES[class_id]

                    detections.append({
                        'class_name': class_name,
                        'conf': conf,
                        'box': [int(x1), int(y1), int(x2), int(y2)]
                    })
                    class_counts[class_name] = class_counts.get(class_name, 0) + 1

        # Update tracker with detections (without counting line)
        try:
            # Convert detections to list of boxes for tracker
            detection_boxes = [[d['box'][0], d['box'][1], d['box'][2], d['box'][3]] for d in detections]
            tracked_vehicles = vehicle_tracker.update(detection_boxes)
        except Exception as e:
            print(f"[ERROR] Tracker update failed: {e}")
            tracked_vehicles = {}
            # Fallback to simple detections
            for det in detections:
                tracked_vehicles[len(tracked_vehicles)] = {
                    'bbox': det['box'],
                    'class': det['class_name'],
                    'center': ((det['box'][0] + det['box'][2]) // 2, (det['box'][1] + det['box'][3]) // 2)
                }

        # Draw tracked vehicles
        for v_id, vehicle in tracked_vehicles.items():
            x1, y1, x2, y2 = vehicle['bbox']
            class_name = vehicle['class']
            color = CLASS_COLORS.get(class_name, (0, 255, 0))
            
            # Draw bounding box
            cv2.rectangle(annotated, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
            
            # Draw ID and class
            display_name = DISPLAY_NAMES.get(class_name, class_name)
            label = f"ID:{v_id} {display_name}"
            (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            cv2.rectangle(annotated, (int(x1), int(y1) - label_h - 10),
                        (int(x1) + label_w, int(y1)), color, -1)
            cv2.putText(annotated, label, (int(x1), int(y1) - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
            
            # Draw center point
            center = vehicle['center']
            cv2.circle(annotated, (int(center[0]), int(center[1])), 4, (255, 255, 255), -1)

        # Add stats overlay (fixed - no blinking)
        overlay = annotated.copy()
        cv2.rectangle(overlay, (0, 0), (350, 100), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, annotated, 0.3, 0, annotated)
        
        cv2.putText(annotated, f"Vehicles: {len(tracked_vehicles)}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(annotated, f"Count Up: {vehicle_tracker.count_up}", (10, 55),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        cv2.putText(annotated, f"Count Down: {vehicle_tracker.count_down}", (10, 80),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        # Encode to JPEG
        _, buffer = cv2.imencode('.jpg', annotated)
        img_base64 = base64.b64encode(buffer).decode('utf-8')

        # Prepare breakdown text
        breakdown_text = ""
        if class_counts:
            breakdown_text = ", ".join([f"{DISPLAY_NAMES.get(cls, cls)}: {count}" for cls, count in class_counts.items()])

        return {
            'image': img_base64,
            'count': len(tracked_vehicles),
            'breakdown': breakdown_text,
            'count_up': vehicle_tracker.count_up,
            'count_down': vehicle_tracker.count_down,
            'total_counted': vehicle_tracker.count_up + vehicle_tracker.count_down
        }

    except Exception as e:
        print(f"[ERROR] Webcam detection failed: {e}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}, 500


@app.route('/save_live_session', methods=['POST'])
def save_live_session():
    """Save live detection session to database"""
    try:
        data = request.get_json()
        report_id = data.get('report_id', str(uuid.uuid4())[:8])
        session_start = data.get('session_start')
        session_end = data.get('session_end')
        total_detections = data.get('total_detections', 0)
        conf_threshold = data.get('confidence_threshold', 0.4)
        stats = data.get('stats', {})
        breakdown = data.get('breakdown', '')
        image_data = None  # Don't save image for live detection
        video_path = data.get('video_path', None)
        vehicle_counts = data.get('vehicle_counts', {})

        print(f"[DEBUG] save_live_session called: report_id={report_id}, video_path={video_path}")
        print(f"[DEBUG] vehicle_counts: {vehicle_counts}")

        # Convert timestamps to datetime objects - handle multiple formats
        from datetime import datetime
        if session_start:
            try:
                # Try standard format
                session_start = datetime.strptime(session_start, '%Y-%m-%d %H:%M:%S')
            except:
                try:
                    # Try browser locale format (e.g., '22/4/2026, 7:08:43 pm')
                    session_start = datetime.strptime(session_start, '%d/%m/%Y, %I:%M:%S %p')
                except:
                    # Fallback to current time
                    session_start = datetime.utcnow()
        else:
            session_start = datetime.utcnow()

        if session_end:
            try:
                # Try standard format
                session_end = datetime.strptime(session_end, '%Y-%m-%d %H:%M:%S')
            except:
                try:
                    # Try browser locale format
                    session_end = datetime.strptime(session_end, '%d/%m/%Y, %I:%M:%S %p')
                except:
                    # Fallback to current time
                    session_end = datetime.utcnow()
        else:
            session_end = datetime.utcnow()

        # Don't use video counts - use live real-time counts instead
        # Video processing counts are duplicates, use sessionStats breakdown instead
        if stats and isinstance(stats, dict) and 'breakdown' in stats:
            breakdown = stats['breakdown']
        
        # Use total_detections from live session (real-time count), not from video
        # Don't override with video counts to avoid duplicates

        # Save to database
        save_live_detection_to_db(report_id, session_start, session_end, total_detections,
                                  conf_threshold, stats, breakdown, image_data, video_path)

        return {'success': True, 'report_id': report_id}
    except Exception as e:
        print(f"[ERROR] Failed to save live session: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}, 500


@app.route('/upload_live_video', methods=['POST'])
def upload_live_video():
    """Upload recorded video from live detection and process with vehicle detection"""
    try:
        if 'video' not in request.files:
            print("[ERROR] No video file provided in request")
            return {'error': 'No video file provided'}, 400
        
        video_file = request.files['video']
        report_id = request.form.get('report_id', str(uuid.uuid4())[:8])
        
        if video_file.filename == '':
            print("[ERROR] Empty video filename")
            return {'error': 'No file selected'}, 400
        
        # Save original video to static/videos directory
        filename = f"live_{report_id}_{int(datetime.utcnow().timestamp())}.webm"
        video_path = os.path.join(STATIC_DIR, filename)
        video_file.save(video_path)
        print(f"[INFO] Original video saved to: {video_path}")
        
        # Check if the video file is valid (not empty)
        file_size = os.path.getsize(video_path)
        print(f"[INFO] Original video file size: {file_size} bytes")
        if file_size < 1000:  # Less than 1KB is likely corrupted
            print(f"[ERROR] Video file is too small ({file_size} bytes), likely corrupted")
            os.remove(video_path)
            return {'error': 'Video file is corrupted or empty. Please try recording again.'}, 400
        
        # Process video with YOLOv8 detection
        processed_filename = f"processed_{report_id}_{int(datetime.utcnow().timestamp())}.mp4"
        processed_path = os.path.join(STATIC_DIR, processed_filename)
        print(f"[INFO] Will process video to: {processed_path}")
        
        # Process video with detections
        try:
            vehicle_counts = process_video_with_detections(video_path, processed_path)
        except Exception as e:
            print(f"[ERROR] Video processing failed: {e}")
            import traceback
            traceback.print_exc()
            # If processing fails, just use the original video
            print(f"[INFO] Using original video as fallback")
            processed_filename = filename
            processed_path = video_path
            vehicle_counts = {'total': 0, 'car': 0, 'motorcycle': 0, 'bus': 0, 'truck': 0}
        
        # Check if processed video was created and is valid
        if not os.path.exists(processed_path):
            print(f"[ERROR] Processed video not created: {processed_path}")
            return {'error': 'Video processing failed - output file not created'}, 500
        
        processed_size = os.path.getsize(processed_path)
        print(f"[INFO] Processed video size: {processed_size} bytes")
        if processed_size < 1000:
            print(f"[WARN] Processed video is too small ({processed_size} bytes), using original")
            processed_filename = filename
            processed_path = video_path
        
        print(f"[INFO] Video processing complete. Final video: {processed_filename}")
        
        # Keep original video as backup (don't delete)
        original_path = filename
        
        return {
            'success': True, 
            'video_path': processed_filename,
            'original_path': original_path,
            'vehicle_counts': vehicle_counts
        }
    except Exception as e:
        print(f"[ERROR] Failed to upload video: {e}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}, 500


def extract_frames_from_video(video_path, max_frames=3):
    """Extract frames from video for PDF generation"""
    import cv2
    
    if not video_path or not os.path.exists(os.path.join(STATIC_DIR, video_path)):
        return []
    
    full_path = os.path.join(STATIC_DIR, video_path)
    cap = cv2.VideoCapture(full_path)
    
    if not cap.isOpened():
        print(f"[WARN] Cannot open video for frame extraction: {full_path}")
        return []
    
    frames = []
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Extract evenly spaced frames
    frame_indices = [int(total_frames * i / max_frames) for i in range(max_frames)]
    
    for frame_idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if ret:
            _, buffer = cv2.imencode('.jpg', frame)
            frames.append(buffer.tobytes())
    
    cap.release()
    print(f"[INFO] Extracted {len(frames)} frames from video: {video_path}")
    return frames


def process_video_with_detections(input_path, output_path):
    """Process video with YOLOv8 vehicle detection and draw bounding boxes"""
    import cv2
    from ultralytics import YOLO
    
    # Vehicle class names
    VEHICLE_CLASSES = {
        2: 'car',
        3: 'motorcycle',
        5: 'bus',
        7: 'truck'
    }
    
    CLASS_COLORS = {
        'car': (0, 255, 0),
        'motorcycle': (255, 0, 0),
        'bus': (0, 0, 255),
        'truck': (255, 255, 0)
    }
    
    # Initialize video capture
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open video: {input_path}")
        return {}
    
    # Get video properties
    fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Initialize video writer with MP4 codec for Raspberry Pi compatibility
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # MP4 codec (works on Raspberry Pi)
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    # Vehicle counts
    vehicle_counts = {
        'car': 0,
        'motorcycle': 0,
        'bus': 0,
        'truck': 0,
        'total': 0
    }
    
    frame_count = 0
    # Process all frames - no limit for live detection
    
    print(f"[INFO] Processing video: {input_path}")
    print(f"[INFO] Video properties: {width}x{height} @ {fps}fps")
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Run YOLO detection
        results = model.predict(frame, imgsz=320, conf=0.4, verbose=False)
        
        # Draw detections on frame
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0].cpu().numpy())
                if class_id in VEHICLE_CLASSES:
                    class_name = VEHICLE_CLASSES[class_id]
                    conf = float(box.conf[0].cpu().numpy())
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                    
                    # Draw bounding box
                    color = CLASS_COLORS.get(class_name, (0, 255, 0))
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    
                    # Draw label
                    label = f"{class_name} {conf:.2f}"
                    cv2.putText(frame, label, (x1, y1 - 10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                    
                    # Count vehicles
                    vehicle_counts[class_name] += 1
                    vehicle_counts['total'] += 1
        
        # Write processed frame
        out.write(frame)
        frame_count += 1
        
        if frame_count % 30 == 0:
            print(f"[INFO] Processed {frame_count} frames...")
    
    cap.release()
    out.release()

    # Check if processed video was actually created
    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        print(f"[ERROR] Processed video not created: {output_path}")
        # Return empty counts since video processing failed
        return {}

    print(f"[INFO] Video processing complete. Total vehicles: {vehicle_counts}")
    print(f"[INFO] Processed video saved to: {output_path}")

    return vehicle_counts


@app.route('/view/<path:filename>')
def view_video(filename):
    """Serve video for inline viewing in browser with proper headers"""
    # Handle 'videos/' prefix in the URL
    if filename.startswith('videos/'):
        filename = filename[7:]  # Remove 'videos/' prefix

    # First check static directory
    static_path = os.path.join(STATIC_DIR, filename)
    if os.path.exists(static_path) and os.path.getsize(static_path) > 0:
        video_path = static_path
    elif hasattr(app, 'temp_videos') and filename in app.temp_videos:
        video_path = app.temp_videos[filename]
        if not os.path.exists(video_path) or os.path.getsize(video_path) == 0:
            return "Video file not ready or empty", 404
    else:
        return "File not found", 404

    # Add cache control headers to prevent caching issues
    response = send_file(
        video_path,
        mimetype='video/mp4',
        as_attachment=False,
        conditional=True  # Support range requests for video seeking
    )
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['Accept-Ranges'] = 'bytes'
    return response


@app.route('/static/videos/<path:filename>')
def serve_video(filename):
    """Serve video files from static/videos directory"""
    video_path = os.path.join(STATIC_DIR, filename)
    if os.path.exists(video_path) and os.path.getsize(video_path) > 0:
        response = send_file(
            video_path,
            mimetype='video/mp4',
            as_attachment=False,
            conditional=True
        )
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        response.headers['Accept-Ranges'] = 'bytes'
        return response
    else:
        return "Video file not found", 404


@app.route('/demo_videos/<path:filename>')
def serve_demo_video(filename):
    """Serve demo videos from demo_videos folder"""
    demo_videos_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'demo_videos')
    video_path = os.path.join(demo_videos_dir, filename)

    if os.path.exists(video_path):
        response = send_file(
            video_path,
            mimetype='video/mp4',
            as_attachment=False,
            conditional=True
        )
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        response.headers['Accept-Ranges'] = 'bytes'
        return response
    else:
        return "Video file not found", 404


# Live Detection Page Template
LIVE_DETECTION_TEMPLATE = """
<!DOCTYPE html>
<html class="light" lang="en">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>Live Detection | Vehicle Intelligence</title>
<!-- Material Symbols -->
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<!-- Google Fonts: Manrope & Inter -->
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;family=Manrope:wght@600;700;800&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<!-- Tailwind CSS -->
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<script id="tailwind-config">
        tailwind.config = {
            darkMode: "class",
            theme: {
                extend: {
                    "colors": {
                        "tertiary-fixed-dim": "#ecbf83",
                        "tertiary": "#341f00",
                        "on-tertiary": "#ffffff",
                        "surface-tint": "#436182",
                        "surface-container-lowest": "#ffffff",
                        "primary-fixed-dim": "#abc9ef",
                        "on-secondary-fixed": "#121c28",
                        "surface-container": "#eeedf0",
                        "outline-variant": "#c3c6ce",
                        "secondary-container": "#d3deef",
                        "on-error": "#ffffff",
                        "surface-container-low": "#f4f3f6",
                        "on-tertiary-fixed-variant": "#5f4110",
                        "tertiary-fixed": "#ffddb3",
                        "surface-dim": "#dad9dd",
                        "surface-bright": "#faf9fc",
                        "tertiary-container": "#4f3303",
                        "primary-container": "#1b3b5a",
                        "surface-container-highest": "#e3e2e5",
                        "on-secondary-container": "#576270",
                        "on-tertiary-fixed": "#291800",
                        "on-tertiary-container": "#c59c63",
                        "error": "#ba1a1a",
                        "outline": "#73777e",
                        "secondary-fixed": "#d8e3f4",
                        "primary": "#002542",
                        "background": "#faf9fc",
                        "surface-variant": "#e3e2e5",
                        "secondary": "#545f6e",
                        "on-error-container": "#93000a",
                        "on-primary": "#ffffff",
                        "inverse-surface": "#2f3033",
                        "error-container": "#ffdad6",
                        "secondary-fixed-dim": "#bcc7d8",
                        "on-secondary-fixed-variant": "#3d4855",
                        "surface": "#faf9fc",
                        "on-surface-variant": "#43474d",
                        "on-secondary": "#ffffff",
                        "on-primary-fixed-variant": "#2a4968",
                        "on-primary-fixed": "#001d35",
                        "inverse-primary": "#abc9ef",
                        "surface-container-high": "#e9e8eb",
                        "on-background": "#1a1c1e",
                        "inverse-on-surface": "#f1f0f3",
                        "primary-fixed": "#d1e4ff",
                        "on-primary-container": "#87a5ca",
                        "on-surface": "#1a1c1e"
                    },
                    "borderRadius": {
                        "DEFAULT": "0.125rem",
                        "lg": "0.25rem",
                        "xl": "0.5rem",
                        "full": "0.75rem"
                    },
                    "fontFamily": {
                        "headline": ["Manrope"],
                        "body": ["Inter"],
                        "label": ["Inter"]
                    }
                }
            }
        }
    </script>
<style>
        .material-symbols-outlined {
            font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
            vertical-align: middle;
        }
        body { font-family: 'Inter', sans-serif; }
        h1, h2, h3 { font-family: 'Manrope', sans-serif; }
        .glass-panel {
            background: rgba(250, 249, 252, 0.7);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
        }
        .hud-scanline {
            background: linear-gradient(to bottom, transparent 50%, rgba(0, 37, 66, 0.05) 51%);
            background-size: 100% 4px;
        }
    </style>
<style>
    body {
      min-height: max(884px, 100dvh);
    }
  </style>
</head>
<body class="bg-surface text-on-surface selection:bg-primary-fixed selection:text-on-primary-fixed min-h-screen pb-24 md:pb-0">
<!-- TopAppBar Execution -->
<header class="fixed top-0 w-full z-50 bg-slate-50/70 backdrop-blur-md shadow-[0px_8px_24px_rgba(0,37,66,0.06)] flex items-center justify-between px-6 h-16 w-full">
<div class="flex items-center gap-3">
<span class="material-symbols-outlined text-blue-900">analytics</span>
<span class="text-xl font-bold tracking-tight text-blue-900">Enterprise Vehicle Intelligence</span>
</div>
<div class="flex items-center gap-6">
<nav class="hidden md:flex gap-6">
<a class="text-slate-500 hover:bg-blue-50 transition-colors px-3 py-1 rounded-lg text-sm" href="/">Upload</a>
<a class="text-blue-900 font-semibold text-sm" href="/live">Real-time</a>
<a class="text-slate-500 hover:bg-blue-50 transition-colors px-3 py-1 rounded-lg text-sm" href="/history">History</a>
</nav>
<div class="flex items-center gap-3 border-l border-outline-variant/20 pl-6">
<div class="flex items-center gap-2">
<span class="material-symbols-outlined text-primary text-sm">account_circle</span>
<span class="text-sm font-semibold text-primary">{{ session.get('username', 'User') }}</span>
</div>
<a href="/logout" class="flex items-center gap-1 text-sm text-red-600 hover:text-red-700 hover:bg-red-50 transition-colors px-3 py-1.5 rounded-lg font-semibold">
<span class="material-symbols-outlined text-sm">logout</span>
Logout
</a>
</div>
</div>
</header>
<main class="max-w-7xl mx-auto px-6 py-12 md:py-16">
<div class="flex flex-col gap-10">
<!-- Header Section -->
<div class="flex flex-col md:flex-row md:items-end justify-between gap-6">
<div>
<div class="flex items-center gap-2 mb-2">
<span class="inline-block w-2 h-2 bg-error rounded-full animate-pulse"></span>
<span class="text-label-md font-bold text-error uppercase tracking-widest text-[10px]">Live Session Active</span>
</div>
<h2 class="text-4xl md:text-5xl font-extrabold tracking-tight text-primary">Live Detection</h2>
<p class="text-on-surface-variant mt-2 text-lg max-w-2xl font-medium opacity-80">Precision monitoring of incoming vehicle streams with millisecond latency.</p>
</div>
<div class="flex gap-4">
<button onclick="startWebcam()" id="startWebcamBtn" class="group flex items-center gap-2 bg-gradient-to-br from-primary to-primary-container text-on-primary px-8 py-3 rounded-md font-bold text-sm shadow-lg hover:shadow-xl transition-all active:scale-95">
<span class="material-symbols-outlined text-[20px]">videocam</span>
                        Start Webcam
                    </button>
<button onclick="stopWebcam()" id="stopWebcamBtn" class="group flex items-center gap-2 bg-surface-container-lowest text-primary px-6 py-3 rounded-md font-semibold text-sm border border-outline-variant/20 shadow-sm hover:shadow-md transition-all active:scale-95 hidden" ondblclick="return false;">
<span class="material-symbols-outlined text-[20px]">videocam_off</span>
                        Stop Webcam
                    </button>
<button onclick="captureFrame()" class="flex items-center gap-2 bg-surface-container-lowest text-primary px-6 py-3 rounded-md font-semibold text-sm border border-outline-variant/20 shadow-sm hover:shadow-md transition-all active:scale-95">
<span class="material-symbols-outlined text-[20px]">screenshot</span>
                        Capture Frame
                    </button>
</div>
</div>
<!-- Bento Grid Main Content -->
<div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
<!-- Primary Video Feed Area -->
<div class="lg:col-span-8 flex flex-col gap-6">
<div class="relative aspect-video bg-inverse-surface rounded-xl overflow-hidden shadow-2xl group border-4 border-surface-container-lowest">
<!-- Video Feed -->
<video id="webcamVideo" autoplay playsinline class="w-full h-full object-cover"></video>
<!-- Canvas for Detection Overlay -->
<canvas id="detectionCanvas" class="absolute inset-0 w-full h-full"></canvas>
<!-- HUD Overlay Components -->
<div class="absolute inset-0 pointer-events-none hud-scanline opacity-10"></div>
<!-- Top HUD Info -->
<div class="absolute top-6 left-6 right-6 flex justify-between items-start z-10">
<div class="glass-panel px-4 py-2 rounded-lg border border-white/20 flex items-center gap-3">
<span class="material-symbols-outlined text-primary">sensors</span>
<div class="flex flex-col">
<span class="text-[10px] font-bold text-primary/60 uppercase tracking-tighter">Signal Quality</span>
<span class="text-xs font-bold text-primary">Ultra HD / 60 FPS</span>
</div>
</div>
<div class="glass-panel px-4 py-2 rounded-lg border border-white/20 flex items-center gap-3">
<span class="material-symbols-outlined text-primary">schedule</span>
<span class="text-xs font-bold text-primary tabular-nums" id="timestamp">00:00:00.00</span>
</div>
</div>
<!-- Detection Boxes (Mockup) -->
<div id="detectionBoxes" class="absolute inset-0 pointer-events-none z-10"></div>
<!-- Bottom HUD Controls -->
<div class="absolute bottom-6 left-6 z-10 flex items-center gap-3">
<div class="flex items-center gap-2 bg-primary px-3 py-1.5 rounded-full text-on-primary">
<span class="material-symbols-outlined text-sm" style="font-variation-settings: 'FILL' 1;">lens</span>
<span class="text-[11px] font-bold uppercase tracking-widest" id="scanStatus">Starting...</span>
</div>
</div>
</div>
<!-- Detection Status Bar -->
<div class="bg-surface-container-lowest rounded-xl p-8 shadow-sm border border-outline-variant/10">
<div class="flex flex-col md:flex-row items-center justify-between gap-6">
<div class="flex items-center gap-6">
<div class="flex flex-col">
<span class="text-label-md text-on-surface-variant mb-1 font-bold tracking-wider text-[11px]">Real-time Status</span>
<h4 class="text-xl font-bold text-primary flex items-center gap-2">
<span class="material-symbols-outlined">check_circle</span>
                                        <span id="vehicleCount">0</span> Vehicles detected
                                    </h4>
</div>
<div class="h-10 w-px bg-outline-variant/30 hidden md:block"></div>
<div class="flex gap-4">
<div class="text-center">
<span class="block text-2xl font-extrabold text-primary" id="carCount">0</span>
<span class="text-[10px] font-bold text-on-surface-variant uppercase">Passenger</span>
</div>
<div class="text-center">
<span class="block text-2xl font-extrabold text-primary" id="truckCount">0</span>
<span class="text-[10px] font-bold text-on-surface-variant uppercase">Commercial</span>
</div>
<div class="h-10 w-px bg-outline-variant/30 hidden md:block"></div>
<div class="text-center">
<span class="block text-2xl font-extrabold text-primary" id="countUp">0</span>
<span class="text-[10px] font-bold text-on-surface-variant uppercase">Up</span>
</div>
<div class="text-center">
<span class="block text-2xl font-extrabold text-primary" id="countDown">0</span>
<span class="text-[10px] font-bold text-on-surface-variant uppercase">Down</span>
</div>
<div class="text-center">
<span class="block text-2xl font-extrabold text-primary" id="totalCounted">0</span>
<span class="text-[10px] font-bold text-on-surface-variant uppercase">Total</span>
</div>
</div>
</div>
<div class="w-full md:w-64 bg-surface-container-low p-4 rounded-lg flex flex-col gap-2">
<div class="flex justify-between items-center">
<span class="text-[10px] font-bold text-on-surface-variant uppercase">Confidence Threshold</span>
<span class="text-[10px] font-extrabold text-primary">85%</span>
</div>
<div class="w-full h-1.5 bg-surface-container-highest rounded-full overflow-hidden">
<div class="h-full bg-primary w-[85%] rounded-full"></div>
</div>
</div>
</div>
</div>
</div>
<!-- Side Technical Analysis Panel -->
<div class="lg:col-span-4 flex flex-col gap-6">
<!-- Metrics Card -->
<div class="bg-surface-container-high rounded-xl p-6 shadow-sm">
<h3 class="text-sm font-bold text-primary uppercase tracking-widest mb-6">Analytical Logs</h3>
<div class="flex flex-col gap-4" id="detectionLogs">
<div class="flex justify-between items-center p-3 bg-surface-container-lowest rounded-lg border border-outline-variant/10">
<div class="flex items-center gap-3">
<span class="material-symbols-outlined text-primary-container">directions_car</span>
<span class="text-sm font-semibold">Waiting for detection...</span>
</div>
</div>
</div>
</div>
<!-- System Performance Card -->
<div class="bg-primary text-on-primary rounded-xl p-6 shadow-xl relative overflow-hidden">
<div class="relative z-10">
<h3 class="text-[10px] font-bold uppercase tracking-[0.2em] mb-4 opacity-70">Engine Performance</h3>
<div class="grid grid-cols-2 gap-4">
<div>
<span class="block text-2xl font-bold font-headline tabular-nums" id="inferenceTime">0ms</span>
<span class="text-[10px] font-medium opacity-60 uppercase">Inference Time</span>
</div>
<div>
<span class="block text-2xl font-bold font-headline tabular-nums">0%</span>
<span class="text-[10px] font-medium opacity-60 uppercase">GPU Load</span>
</div>
</div>
<div class="mt-6 pt-6 border-t border-white/10">
<div class="flex items-center gap-2 mb-3">
<span class="material-symbols-outlined text-sm">cloud_done</span>
<span class="text-xs font-bold uppercase tracking-wider">Cloud Synchronized</span>
</div>
<p class="text-[11px] opacity-60 leading-relaxed font-medium">Model v4.2-L is currently processing live edge data with local redundancy enabled.</p>
</div>
</div>
<!-- Background Accents -->
<div class="absolute -bottom-10 -right-10 w-40 h-40 bg-primary-container rounded-full blur-3xl opacity-40"></div>
</div>
<!-- Configuration Shortcut -->
<button class="w-full py-4 px-6 border-2 border-dashed border-outline-variant/30 rounded-xl text-on-surface-variant hover:border-primary-container/40 hover:text-primary transition-all flex items-center justify-between group">
<div class="flex items-center gap-3">
<span class="material-symbols-outlined group-hover:rotate-45 transition-transform">tune</span>
<span class="text-sm font-bold uppercase tracking-wide">Adjust Sensitivity</span>
</div>
<span class="material-symbols-outlined text-sm">chevron_right</span>
</button>
</div>
</div>
</div>

<!-- Result Section (Hidden by default) -->
<div id="resultSection" class="hidden mt-10 bg-surface-container-lowest rounded-xl p-8 shadow-sm border border-outline-variant/10">
<div class="flex items-center justify-between mb-6">
<h3 class="text-2xl font-bold text-primary">Detection Result</h3>
<span class="text-xs font-bold uppercase tracking-wider px-3 py-1 rounded bg-primary/10 text-primary">Live Detection</span>
</div>

<!-- Video Result -->
<div id="resultVideoContainer" class="mb-6">
<video id="resultVideo" controls class="w-full rounded-lg shadow-md"></video>
</div>

<!-- Stats -->
<div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
<div class="bg-surface-container p-4 rounded-lg">
<div class="text-3xl font-extrabold text-primary" id="resultVehicleCount">0</div>
<div class="text-xs text-on-surface-variant uppercase">Total Vehicles</div>
</div>
<div class="bg-surface-container p-4 rounded-lg">
<div class="text-3xl font-extrabold text-primary" id="resultCarCount">0</div>
<div class="text-xs text-on-surface-variant uppercase">Cars</div>
</div>
<div class="bg-surface-container p-4 rounded-lg">
<div class="text-3xl font-extrabold text-primary" id="resultMotorcycleCount">0</div>
<div class="text-xs text-on-surface-variant uppercase">Motorcycles</div>
</div>
<div class="bg-surface-container p-4 rounded-lg">
<div class="text-3xl font-extrabold text-primary" id="resultTruckCount">0</div>
<div class="text-xs text-on-surface-variant uppercase">Trucks</div>
</div>
</div>

<!-- Breakdown -->
<div id="resultBreakdown" class="bg-surface-container p-4 rounded-lg">
<h4 class="text-sm font-bold text-primary mb-2">Vehicle Breakdown</h4>
<div id="breakdownText" class="text-sm text-on-surface-variant"></div>
</div>

<!-- Actions -->
<div class="flex gap-4 mt-6">
<a id="viewReportLink" href="#" target="_blank" class="flex items-center gap-2 px-6 py-3 bg-primary text-white font-semibold rounded-lg hover:bg-primary-container transition-colors">
<span class="material-symbols-outlined">visibility</span>
View Report
</a>
<a id="downloadPdfLink" href="#" target="_blank" class="flex items-center gap-2 px-6 py-3 bg-surface-container text-primary font-semibold rounded-lg border border-outline-variant/20 hover:bg-surface-container-low transition-colors">
<span class="material-symbols-outlined">download</span>
Download PDF
</a>
</div>
</div>

</main>
<!-- BottomNavBar Execution -->
<nav class="fixed bottom-0 left-0 w-full h-20 bg-white dark:bg-slate-950 flex justify-around items-center px-4 pb-safe z-50 md:hidden shadow-[0px_-4px_20px_rgba(0,37,66,0.04)] rounded-t-xl">
<a class="flex flex-col items-center justify-center text-slate-400 dark:text-slate-500 px-6 py-2 transition-all active:scale-90 duration-200" href="/">
<span class="material-symbols-outlined mb-1">upload_file</span>
<span class="text-[11px] font-semibold tracking-wide Inter uppercase">Upload</span>
</a>
<a class="flex flex-col items-center justify-center bg-[#d1e4ff] dark:bg-blue-900/40 text-[#002542] dark:text-blue-100 rounded-xl px-6 py-2 transition-all active:scale-90 duration-200" href="/live">
<span class="material-symbols-outlined mb-1">videocam</span>
<span class="text-[11px] font-semibold tracking-wide Inter uppercase">Real-time</span>
</a>
<a class="flex flex-col items-center justify-center text-slate-400 dark:text-slate-500 px-6 py-2 transition-all active:scale-90 duration-200" href="/history">
<span class="material-symbols-outlined mb-1">history</span>
<span class="text-[11px] font-semibold tracking-wide Inter uppercase">History</span>
</a>
</nav>
<script>
    let stream = null;
    let isRunning = false;
    let detectionInterval = null;
    let mediaRecorder = null;
    let recordedChunks = [];
    let isRecording = false;

    async function startWebcam() {
        try {
            const video = document.getElementById('webcamVideo');
            stream = await navigator.mediaDevices.getUserMedia({ video: true });
            video.srcObject = stream;
            isRunning = true;
            sessionStartTime = new Date().toLocaleString();
            totalDetections = 0;
            sessionStats = {};
            document.getElementById('scanStatus').textContent = 'Scanning...';
            document.getElementById('startWebcamBtn').classList.add('hidden');
            document.getElementById('stopWebcamBtn').classList.remove('hidden');
            
            // Start video recording
            startVideoRecording();
            
            startDetection();
            updateTimestamp();
        } catch (err) {
            console.error('Error accessing webcam:', err);
            alert('Could not access webcam. Please ensure camera permissions are granted.');
        }
    }

    function startVideoRecording() {
        recordedChunks = [];
        const canvas = document.getElementById('detectionCanvas');
        const video = document.getElementById('webcamVideo');
        
        // Wait for video to be ready
        video.onloadedmetadata = function() {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
        };
        
        // Capture canvas stream at 30 FPS
        const canvasStream = canvas.captureStream(30);
        const options = { mimeType: 'video/webm;codecs=vp9' };
        
        try {
            mediaRecorder = new MediaRecorder(canvasStream, options);
        } catch (e) {
            console.warn('VP9 not supported, trying VP8');
            mediaRecorder = new MediaRecorder(canvasStream, { mimeType: 'video/webm;codecs=vp8' });
        }
        
        mediaRecorder.ondataavailable = function(event) {
            if (event.data.size > 0) {
                recordedChunks.push(event.data);
                console.log('[INFO] Chunk received, size:', event.data.size);
            }
        };
        
        mediaRecorder.start(100); // Collect data every 100ms
        isRecording = true;
        console.log('[INFO] Video recording started from canvas with detections');
    }

    async function stopVideoRecording() {
        if (mediaRecorder && isRecording) {
            mediaRecorder.stop();
            isRecording = false;
            
            return new Promise((resolve) => {
                mediaRecorder.onstop = async function() {
                    const blob = new Blob(recordedChunks, { type: 'video/webm' });
                    const formData = new FormData();
                    formData.append('video', blob, `live_${Date.now()}.webm`);
                    formData.append('report_id', 'live_' + Math.random().toString(36).substr(2, 8));
                    
                    try {
                        const response = await fetch('/upload_live_video', {
                            method: 'POST',
                            body: formData
                        });
                        const result = await response.json();
                        console.log('[INFO] Video uploaded:', result);
                        resolve(result);
                    } catch (error) {
                        console.error('[ERROR] Failed to upload video:', error);
                        resolve(null);
                    }
                };
            });
        }
        return null;
    }

    async function stopWebcam() {
        const stopBtn = document.getElementById('stopWebcamBtn');
        stopBtn.disabled = true;
        stopBtn.innerHTML = '<span class="material-symbols-outlined text-[20px]">hourglass_empty</span>Stopping...';
        
        // Stop webcam immediately
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            stream = null;
        }
        isRunning = false;
        if (detectionInterval) {
            clearInterval(detectionInterval);
            detectionInterval = null;
        }
        document.getElementById('scanStatus').textContent = 'Stopped';
        const video = document.getElementById('webcamVideo');
        video.srcObject = null;
        document.getElementById('detectionBoxes').innerHTML = '';
        document.getElementById('startWebcamBtn').classList.remove('hidden');
        document.getElementById('stopWebcamBtn').classList.add('hidden');

        // Stop video recording and upload in background
        stopVideoRecording().then(videoResult => {
            console.log('[INFO] Video recording stopped:', videoResult);
            // Save live session in background
            saveLiveSession(videoResult);
            // Show result section
            showResultSection(videoResult);
            stopBtn.disabled = false;
            stopBtn.innerHTML = '<span class="material-symbols-outlined text-[20px]">videocam_off</span>Stop Webcam';
        }).catch(error => {
            console.error('[ERROR] Failed to stop video recording:', error);
            // Still save session even if video failed
            saveLiveSession(null);
            stopBtn.disabled = false;
            stopBtn.innerHTML = '<span class="material-symbols-outlined text-[20px]">videocam_off</span>Stop Webcam';
        });
    }

    function showResultSection(videoResult) {
        if (!videoResult || !videoResult.success) {
            console.log('[WARN] No video result to show');
            return;
        }

        console.log('[INFO] Showing result section with video:', videoResult);
        const resultSection = document.getElementById('resultSection');
        const resultVideo = document.getElementById('resultVideo');

        // Show result section
        resultSection.classList.remove('hidden');

        // Set video source
        if (videoResult.video_path) {
            // Use static/videos/ prefix for video files
            const videoUrl = '/static/videos/' + videoResult.video_path;
            console.log('[INFO] Setting video source to:', videoUrl);
            resultVideo.src = videoUrl;
            resultVideo.load(); // Explicitly load the video
            resultVideo.play().catch(e => console.log('[WARN] Auto-play prevented:', e));
        } else {
            console.log('[WARN] No video_path in videoResult');
        }

        // Update stats
        const vehicleCounts = videoResult.vehicle_counts || {};
        document.getElementById('resultVehicleCount').textContent = vehicleCounts.total || totalDetections || 0;
        document.getElementById('resultCarCount').textContent = vehicleCounts.car || 0;
        document.getElementById('resultMotorcycleCount').textContent = vehicleCounts.motorcycle || 0;
        document.getElementById('resultTruckCount').textContent = vehicleCounts.truck || 0;

        // Update breakdown
        const breakdownText = document.getElementById('breakdownText');
        if (vehicleCounts) {
            breakdownText.textContent = `Car: ${vehicleCounts.car || 0}, Motorcycle: ${vehicleCounts.motorcycle || 0}, Bus: ${vehicleCounts.bus || 0}, Truck: ${vehicleCounts.truck || 0}`;
        } else {
            breakdownText.textContent = sessionStats.breakdown || 'No breakdown available';
        }

        // Note: View Report and Download PDF links will be set after saveLiveSession completes
    }

    let sessionStartTime = null;
    let totalDetections = 0;
    let sessionStats = {};
    let capturedFrame = null; // Store captured frame for saving

    async function saveLiveSession(videoResult = null) {
        // Save even if 0 detections - user should see all sessions
        const sessionEndTime = new Date().toLocaleString();
        const reportId = 'live_' + Math.random().toString(36).substr(2, 8);

        // Use processed video path if available, else null
        const processedVideoPath = videoResult && videoResult.success ? videoResult.video_path : null;
        const vehicleCounts = videoResult && videoResult.success ? videoResult.vehicle_counts : {};

        try {
            const response = await fetch('/save_live_session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    report_id: reportId,
                    session_start: sessionStartTime,
                    session_end: sessionEndTime,
                    total_detections: totalDetections,
                    confidence_threshold: 0.4,
                    stats: sessionStats,
                    breakdown: sessionStats.breakdown || '',
                    image_data: null, // Don't save image for live detection
                    video_path: processedVideoPath, // Send processed video path
                    vehicle_counts: vehicleCounts // Send vehicle counts by type
                })
            });
            const data = await response.json();
            if (data.success) {
                console.log('[INFO] Live session saved to database:', data.report_id);
                // Set view report and download PDF links
                document.getElementById('viewReportLink').href = '/view_report/' + data.report_id;
                document.getElementById('downloadPdfLink').href = '/generate_pdf/' + data.report_id;
                return { ...videoResult, report_id: data.report_id };
            } else {
                console.error('[ERROR] Failed to save live session:', data.error);
                return videoResult;
            }
        } catch (error) {
            console.error('[ERROR] Failed to save live session:', error);
            return videoResult;
        }
    }

    function updateTimestamp() {
        if (!isRunning) return;
        const now = new Date();
        const timeStr = now.toTimeString().split(' ')[0] + '.' + Math.floor(now.getMilliseconds() / 10).toString().padStart(2, '0');
        document.getElementById('timestamp').textContent = timeStr;
        requestAnimationFrame(updateTimestamp);
    }

    function startDetection() {
        // Real detection using backend YOLO model
        // Increased interval to reduce lag/rush (500ms instead of 100ms)
        detectionInterval = setInterval(() => {
            if (!isRunning) return;
            processFrame();
        }, 500);
    }

    async function processFrame() {
        const video = document.getElementById('webcamVideo');
        const canvas = document.getElementById('detectionCanvas');
        const ctx = canvas.getContext('2d');

        // Set canvas size to match video
        canvas.width = video.videoWidth || 640;
        canvas.height = video.videoHeight || 480;

        // Draw video frame to canvas
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        // Capture frame for saving (use lower quality for performance)
        capturedFrame = canvas.toDataURL('image/jpeg', 0.5);

        // Get frame data for detection
        const frameData = capturedFrame;

        try {
            const formData = new FormData();
            formData.append('image', frameData);
            formData.append('confidence', '0.4');

            const response = await fetch('/webcam_detect', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const result = await response.json();

                if (result.image) {
                    // Draw detection result
                    const img = new Image();
                    img.onload = function() {
                        ctx.clearRect(0, 0, canvas.width, canvas.height);
                        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                    };
                    img.src = 'data:image/jpeg;base64,' + result.image;

                    // Update stats
                    document.getElementById('vehicleCount').textContent = result.count;
                    document.getElementById('inferenceTime').textContent = '15ms';

                    // Update counting stats if available
                    if (result.count_up !== undefined) {
                        document.getElementById('countUp').textContent = result.count_up;
                        document.getElementById('countDown').textContent = result.count_down;
                        document.getElementById('totalCounted').textContent = result.total_counted;
                    }

                    // Track session statistics
                    totalDetections += result.count;
                    sessionStats = {
                        count: totalDetections,
                        breakdown: result.breakdown,
                        time: (Date.now() - new Date(sessionStartTime)) / 1000 + 's'
                    };

                    // Parse breakdown to update counts
                    let carCount = 0;
                    let truckCount = 0;
                    const breakdown = result.breakdown || '';

                    if (breakdown.includes('Car')) {
                        const match = breakdown.match(/Car: *([0-9]+)/);
                        if (match) carCount = parseInt(match[1]);
                    }
                    if (breakdown.includes('Truck')) {
                        const match = breakdown.match(/Truck: *([0-9]+)/);
                        if (match) truckCount = parseInt(match[1]);
                    }
                    if (breakdown.includes('Motorcycle')) {
                        const match = breakdown.match(/Motorcycle: *([0-9]+)/);
                        if (match) carCount += parseInt(match[1]); // Add to passenger count
                    }
                    if (breakdown.includes('Bus')) {
                        const match = breakdown.match(/Bus: *([0-9]+)/);
                        if (match) truckCount += parseInt(match[1]); // Add to commercial count
                    }

                    document.getElementById('carCount').textContent = carCount;
                    document.getElementById('truckCount').textContent = truckCount;
                    document.getElementById('scanStatus').textContent = result.count > 0 ? 'DETECTING' : 'Scanning...';

                    // Update detection logs
                    updateDetectionLogs(breakdown);
                }
            }
        } catch (err) {
            console.error('[ERROR] Frame processing error:', err);
        }
    }

    function updateDetectionLogs(breakdown) {
        const logs = document.getElementById('detectionLogs');
        logs.innerHTML = '';

        if (!breakdown || breakdown.trim() === '') {
            logs.innerHTML = `
                <div class="flex justify-between items-center p-3 bg-surface-container-lowest rounded-lg border border-outline-variant/10">
                    <div class="flex items-center gap-3">
                        <span class="material-symbols-outlined text-primary-container">visibility</span>
                        <span class="text-sm font-semibold">Scanning for vehicles...</span>
                    </div>
                </div>
            `;
            return;
        }

        // Parse breakdown and create log entries
        const items = breakdown.split(', ');
        items.forEach(item => {
            const [name, countStr] = item.split(': ');
            const count = parseInt(countStr);
            
            let icon = 'directions_car';
            if (name.includes('Motorcycle')) icon = 'two_wheeler';
            else if (name.includes('Bus')) icon = 'directions_bus';
            else if (name.includes('Truck')) icon = 'local_shipping';

            const logItem = document.createElement('div');
            logItem.className = 'flex justify-between items-center p-3 bg-surface-container-lowest rounded-lg border border-outline-variant/10';
            logItem.innerHTML = `
                <div class="flex items-center gap-3">
                    <span class="material-symbols-outlined text-primary-container">${icon}</span>
                    <span class="text-sm font-semibold">${name}</span>
                </div>
                <span class="text-xs font-bold text-primary px-2 py-1 bg-primary-fixed rounded">${count}</span>
            `;
            logs.appendChild(logItem);
        });
    }

    function captureFrame() {
        const video = document.getElementById('webcamVideo');
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext('2d').drawImage(video, 0, 0);
        
        const link = document.createElement('a');
        link.download = 'capture_' + Date.now() + '.png';
        link.href = canvas.toDataURL();
        link.click();
    }

    // Start webcam automatically when page loads
    window.addEventListener('load', startWebcam);

    // Stop webcam when page is unloaded
    window.addEventListener('beforeunload', stopWebcam);
</script>
</body>
</html>
"""


@app.route('/test')
def test_route():
    """Test route to verify routing works"""
    return "Test route is working!"


@app.route('/debug_session')
def debug_session():
    """Debug route to check session and user data"""
    import json
    user_id = session.get('user_id')
    username = session.get('username')
    
    result = {
        'session_user_id': user_id,
        'session_username': username,
        'session_keys': list(session.keys()),
    }
    
    if user_id:
        db = get_db()
        if db:
            try:
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    result['db_user_found'] = True
                    result['db_user_id'] = user.id
                    result['db_username'] = user.username
                    result['db_email'] = user.email
                else:
                    result['db_user_found'] = False
                    result['db_error'] = f'No user with id {user_id}'
                db.close()
            except Exception as e:
                result['db_error'] = str(e)
        else:
            result['db_error'] = 'No database session'
    
    return json.dumps(result, indent=2, default=str)


@app.route('/live')
@login_required
def live_detection():
    """Render the live detection page"""
    print("[DEBUG] Live detection route accessed")
    return render_template_string(LIVE_DETECTION_TEMPLATE)


# History Page Template
VIEW_REPORT_TEMPLATE = """
<!DOCTYPE html>
<html class="light" lang="en">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>View Report | Vehicle Intelligence</title>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;family=Manrope:wght@600;700;800&amp;display=swap" rel="stylesheet"/>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<script id="tailwind-config">
        tailwind.config = {
            darkMode: "class",
            theme: {
                extend: {
                    "colors": {
                        "primary": "#002542",
                        "primary-container": "#1b3b5a",
                        "surface": "#faf9fc",
                        "surface-container-lowest": "#ffffff",
                        "surface-container-low": "#f4f3f6",
                        "surface-container": "#eeedf0",
                        "on-surface": "#1a1c1e",
                        "on-surface-variant": "#43474d",
                        "outline-variant": "#c3c6ce",
                    },
                    "borderRadius": {
                        "DEFAULT": "0.125rem",
                        "lg": "0.25rem",
                        "xl": "0.5rem",
                        "full": "0.75rem"
                    },
                    "fontFamily": {
                        "headline": ["Manrope"],
                        "body": ["Inter"],
                        "label": ["Inter"]
                    }
                }
            }
        }
    </script>
<style>
        .material-symbols-outlined {
            font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
        }
        body { font-family: 'Inter', sans-serif; }
        h1, h2, h3 { font-family: 'Manrope', sans-serif; }
    </style>
</head>
<body class="bg-surface text-on-surface min-h-screen">
<!-- TopAppBar -->
<header class="fixed top-0 w-full z-50 bg-slate-50/70 backdrop-blur-md shadow-[0px_8px_24px_rgba(0,37,66,0.06)] flex items-center justify-between px-6 h-16">
<div class="flex items-center gap-3">
<span class="material-symbols-outlined text-blue-900">analytics</span>
<span class="text-xl font-bold tracking-tight text-blue-900">Enterprise Vehicle Intelligence</span>
</div>
<div class="flex items-center gap-6">
<a href="/history" class="flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-red-600 hover:bg-red-50 transition-colors px-3 py-1.5 rounded-lg">
<span class="material-symbols-outlined text-lg">arrow_back</span>
Back to History
</a>
</div>
</header>

<main class="max-w-7xl mx-auto px-6 py-20">
<div class="flex flex-col gap-8">
<!-- Header -->
<div>
<h2 class="text-3xl font-extrabold text-primary">Detection Report</h2>
<p class="text-on-surface-variant mt-2">Report ID: {{ report.report_id }}</p>
</div>

<!-- Report Details -->
<div class="bg-surface-container-lowest rounded-xl p-6 shadow-sm border border-outline-variant/10">
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
<div>
<p class="text-sm text-on-surface-variant font-medium">Timestamp</p>
<p class="text-lg font-semibold text-primary">{{ report.timestamp }}</p>
</div>
<div>
<p class="text-sm text-on-surface-variant font-medium">Detection Type</p>
<p class="text-lg font-semibold text-primary">{{ report.detection_type|title }}</p>
</div>
<div>
<p class="text-sm text-on-surface-variant font-medium">Vehicle Count</p>
<p class="text-lg font-semibold text-primary">{{ report.vehicle_count }}</p>
</div>
<div>
<p class="text-sm text-on-surface-variant font-medium">Processing Time</p>
<p class="text-lg font-semibold text-primary">{{ report.processing_time }}</p>
</div>
<div>
<p class="text-sm text-on-surface-variant font-medium">Confidence Threshold</p>
<p class="text-lg font-semibold text-primary">{{ report.confidence_threshold }}</p>
</div>
</div>
</div>

<!-- Detection Image/Video -->
{% if report.video_path %}
<div class="bg-surface-container-lowest rounded-xl p-6 shadow-sm border border-outline-variant/10">
<h3 class="text-xl font-bold text-primary mb-4">Detection Video</h3>
<video controls class="w-full rounded-lg" src="/view/videos/{{ report.video_path }}"></video>
</div>
{% elif report.image_data %}
<div class="bg-surface-container-lowest rounded-xl p-6 shadow-sm border border-outline-variant/10">
<h3 class="text-xl font-bold text-primary mb-4">Detection Image</h3>
{% if report.image_data.startswith('data:') %}
<img src="{{ report.image_data }}" class="w-full rounded-lg" alt="Detection Result">
{% else %}
<img src="data:image/jpeg;base64,{{ report.image_data }}" class="w-full rounded-lg" alt="Detection Result">
{% endif %}
</div>
{% endif %}

<!-- Breakdown -->
{% if report.breakdown %}
<div class="bg-surface-container-lowest rounded-xl p-6 shadow-sm border border-outline-variant/10">
<h3 class="text-xl font-bold text-primary mb-4">Vehicle Breakdown</h3>
<div class="flex flex-wrap gap-3">
{% for class_name, count in report.breakdown.items() %}
<span class="px-4 py-2 bg-surface-container rounded-lg text-sm font-semibold text-primary">
{{ class_name|title }}: {{ count }}
</span>
{% endfor %}
</div>
</div>
{% endif %}

<!-- Actions -->
<div class="flex gap-4">
<a href="/generate_pdf/{{ report.report_id }}" class="flex items-center gap-2 px-6 py-3 bg-primary text-white font-semibold rounded-lg hover:bg-primary-container transition-colors">
<span class="material-symbols-outlined">download</span>
Download PDF
</a>
</div>
</div>
</main>
</body>
</html>
"""

HISTORY_TEMPLATE = """
<!DOCTYPE html>
<html class="light" lang="en">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>History | Vehicle Intelligence</title>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;family=Manrope:wght@600;700;800&amp;display=swap" rel="stylesheet"/>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<script id="tailwind-config">
        tailwind.config = {
            darkMode: "class",
            theme: {
                extend: {
                    "colors": {
                        "primary": "#002542",
                        "primary-container": "#1b3b5a",
                        "surface": "#faf9fc",
                        "surface-container-lowest": "#ffffff",
                        "surface-container-low": "#f4f3f6",
                        "surface-container": "#eeedf0",
                        "on-surface": "#1a1c1e",
                        "on-surface-variant": "#43474d",
                        "outline-variant": "#c3c6ce",
                    },
                    "borderRadius": {
                        "DEFAULT": "0.125rem",
                        "lg": "0.25rem",
                        "xl": "0.5rem",
                        "full": "0.75rem"
                    },
                    "fontFamily": {
                        "headline": ["Manrope"],
                        "body": ["Inter"],
                        "label": ["Inter"]
                    }
                }
            }
        }
    </script>
<style>
        .material-symbols-outlined {
            font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
        }
        body { font-family: 'Inter', sans-serif; }
        h1, h2, h3 { font-family: 'Manrope', sans-serif; }
    </style>
</head>
<body class="bg-surface text-on-surface min-h-screen">
<!-- TopAppBar -->
<header class="fixed top-0 w-full z-50 bg-slate-50/70 backdrop-blur-md shadow-[0px_8px_24px_rgba(0,37,66,0.06)] flex items-center justify-between px-6 h-16 w-full">
<div class="flex items-center gap-3">
<span class="material-symbols-outlined text-blue-900">analytics</span>
<span class="text-xl font-bold tracking-tight text-blue-900">Enterprise Vehicle Intelligence</span>
</div>
<div class="flex items-center gap-6">
<nav class="hidden md:flex gap-6">
<a class="text-slate-500 hover:bg-blue-50 transition-colors px-3 py-1 rounded-lg text-sm" href="/">Upload</a>
<a class="text-slate-500 hover:bg-blue-50 transition-colors px-3 py-1 rounded-lg text-sm" href="/live">Real-time</a>
<a class="text-blue-900 font-semibold text-sm" href="/history">History</a>
</nav>
<div class="flex items-center gap-3 border-l border-slate-200 pl-6">
<div class="flex items-center gap-2">
<span class="material-symbols-outlined text-slate-600 text-xl">person</span>
<span class="text-sm font-medium text-slate-700">test</span>
</div>
<a href="/logout" class="flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-red-600 hover:bg-red-50 transition-colors px-3 py-1.5 rounded-lg">
<span class="material-symbols-outlined text-lg">logout</span>
Logout
</a>
</div>
</div>
</header>
<main class="max-w-7xl mx-auto px-6 py-20">
<div class="flex flex-col gap-8">
<!-- Header -->
<div class="flex justify-between items-center">
<div>
<h2 class="text-3xl font-extrabold text-primary">Past Detections</h2>
<p class="text-on-surface-variant mt-2">View your vehicle detection history</p>
</div>
<div class="text-sm text-slate-500">
<span id="totalCount">0</span> detections
</div>
</div>

<!-- History List -->
<div class="space-y-4" id="historyList">
{% if history %}
{% for item in history %}
<div class="bg-surface-container-lowest rounded-xl p-6 shadow-sm border border-outline-variant/10 hover:border-primary/20 transition-all">
<div class="flex flex-col md:flex-row gap-6">
<!-- Thumbnail -->
<div class="flex-shrink-0">
{% if item.detection_type == 'live' %}
{% if item.video_path %}
<video src="/view/{{ item.video_path }}" class="w-32 h-24 object-cover rounded-lg" controls></video>
{% else %}
<div class="w-32 h-24 bg-surface-container rounded-lg flex items-center justify-center text-xs text-slate-500 text-center p-2">
No Video
</div>
{% endif %}
{% elif item.video_path %}
<video src="/view/{{ item.video_path }}" class="w-32 h-24 object-cover rounded-lg" controls></video>
{% elif item.image_data %}
<img src="{{ item.image_data }}" class="w-32 h-24 object-cover rounded-lg" loading="lazy" alt="Detection">
{% elif item.stats and item.stats.first_frame %}
<img src="{{ item.stats.first_frame }}" class="w-32 h-24 object-cover rounded-lg" loading="lazy" alt="Frame">
{% else %}
<div class="w-32 h-24 bg-surface-container rounded-lg flex items-center justify-center">
<span class="material-symbols-outlined text-slate-400">image</span>
</div>
{% endif %}
</div>

<!-- Details -->
<div class="flex-grow">
<div class="flex items-start justify-between gap-4">
<div>
<div class="flex items-center gap-2 mb-2">
<span class="text-xs font-bold uppercase tracking-wider px-2 py-1 rounded bg-primary/10 text-primary">
{{ 'Live' if item.detection_type == 'live' else ('Video' if item.input_type == 'video' else 'Image') }}
</span>
<span class="text-xs text-slate-500">{{ item.timestamp }}</span>
</div>
<h3 class="text-lg font-bold text-primary">{{ item.message }}</h3>
</div>
<div class="text-right">
<div class="text-2xl font-extrabold text-primary">{{ item.stats.count if item.stats else 0 }}</div>
<div class="text-xs text-slate-500 uppercase">Vehicles</div>
</div>
</div>

{% if item.stats and item.stats.breakdown %}
<div class="mt-3 flex flex-wrap gap-2">
{% for class_name, count in item.stats.breakdown.items() %}
<span class="text-xs font-semibold px-2 py-1 bg-surface-container rounded text-on-surface-variant">
{{ class_name|title }}: {{ count }}
</span>
{% endfor %}
</div>
{% endif %}

<div class="mt-4 flex gap-3">
<a href="/generate_pdf/{{ item.id }}" target="_blank" class="text-sm font-semibold text-primary hover:text-primary-container transition-colors">
Download Report
</a>
<a href="/view_report/{{ item.id }}" target="_blank" class="text-sm font-semibold text-primary hover:text-primary-container transition-colors">
View Report
</a>
{% if item.video_path %}
<a href="/view/videos/{{ item.video_path }}" target="_blank" class="text-sm font-semibold text-primary hover:text-primary-container transition-colors">
View Video
</a>
{% endif %}
<button onclick="deleteDetection('{{ item.id }}')" class="text-sm font-semibold text-red-600 hover:text-red-700 transition-colors">
Delete
</button>
</div>
</div>
</div>
</div>
{% endfor %}
{% else %}
<div class="bg-surface-container-lowest rounded-xl p-12 text-center border border-outline-variant/10">
<span class="material-symbols-outlined text-6xl text-slate-300">history</span>
<h3 class="text-xl font-bold text-primary mt-4">No Detection History</h3>
<p class="text-slate-500 mt-2">Upload images or videos to see your detection history here</p>
<a href="/" class="inline-flex items-center gap-2 mt-6 px-6 py-3 bg-primary text-white font-semibold rounded-lg hover:bg-primary-container transition-colors">
<span class="material-symbols-outlined">upload</span>
Start Detection
</a>
</div>
{% endif %}
</div>
</div>
</main>

<script>
function deleteDetection(reportId) {
    if (confirm('Are you sure you want to delete this detection?')) {
        fetch(`/delete_detection/${reportId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Failed to delete: ' + data.error);
            }
        })
        .catch(error => {
            alert('Error: ' + error);
        });
    }
}
</script>
</body>
</html>
"""


@app.route('/history')
@login_required
def history_page():
    """Render the history page with all past detections"""
    print("[DEBUG] History route accessed")
    history = get_detection_history_from_db(limit=50)
    print(f"[DEBUG] History entries: {len(history)}")
    
    # Debug: Check first entry data
    if history:
        print(f"[DEBUG] First entry keys: {history[0].keys()}")
        print(f"[DEBUG] First entry has image_data: {'image_data' in history[0]}")
        print(f"[DEBUG] First entry image_data length: {len(history[0].get('image_data', '')) if history[0].get('image_data') else 0}")
        print(f"[DEBUG] First entry has video_path: {'video_path' in history[0]}")
        print(f"[DEBUG] First entry video_path: {history[0].get('video_path')}")
    
    return render_template_string(HISTORY_TEMPLATE, history=history)


def main():
    # Initialize database connection and tables
    init_db()

    print("="*50)
    print("Vehicle Detection Web App")
    print("="*50)
    print("Open your browser and go to: http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    print("="*50)
    app.run(host='0.0.0.0', port=5000, debug=False)


if __name__ == '__main__':
    main()
