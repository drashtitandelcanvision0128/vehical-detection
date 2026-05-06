"""
Authentication Routes
Contains login, register, and logout route logic

DEPRECATED: This module is NOT used by the application.
All auth routes are defined inline in web_test_app.py.
This file is kept for reference only.
"""
from flask import render_template_string, request, flash, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from models import User

# Import templates from separate file
try:
    from auth_templates import LOGIN_TEMPLATE, REGISTER_TEMPLATE
except ImportError:
    # Fallback templates if import fails
    LOGIN_TEMPLATE = "<h1>Login Page</h1>"
    REGISTER_TEMPLATE = "<h1>Register Page</h1>"

# Global variable for get_db function - will be set during initialization
_get_db_func = None

def login_required(f):
    """Decorator to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def register_routes(app, get_db):
    """Register authentication routes with the Flask app"""
    global _get_db_func
    _get_db_func = get_db
    
    # Define routes directly on the app
    app.add_url_rule('/login', 'login', login, methods=['GET', 'POST'])
    app.add_url_rule('/register', 'register', register, methods=['GET', 'POST'])
    app.add_url_rule('/logout', 'logout', logout)


def login():
    """Login page"""
    # If user is already logged in, redirect to index
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        db = _get_db_func()
        if not db:
            flash('Database connection error. Please try again.', 'error')
            return render_template_string(LOGIN_TEMPLATE)
        
        try:
            user = db.query(User).filter(User.email == email).first()
            if user and check_password_hash(user.password_hash, password):
                session['user_id'] = user.id
                session['username'] = user.username
                flash('Login successful!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid email or password.', 'error')
        except Exception as e:
            print(f"[ERROR] Login error: {e}")
            flash('Login failed. Please try again.', 'error')
        finally:
            db.close()
    
    return render_template_string(LOGIN_TEMPLATE)


def register():
    """Registration page"""
    # If user is already logged in, redirect to index
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
        
        db = _get_db_func()
        if not db:
            flash('Database connection error. Please try again.', 'error')
            return render_template_string(REGISTER_TEMPLATE)
        
        try:
            # Check if user already exists
            existing_user = db.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first()
            
            if existing_user:
                flash('Username or email already exists.', 'error')
                return render_template_string(REGISTER_TEMPLATE)
            
            # Create new user
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


def logout():
    """Logout user"""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))
