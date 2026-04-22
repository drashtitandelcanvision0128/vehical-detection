"""
Script to create the users table in the database
"""
from sqlalchemy import create_engine
from models import Base
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Database URL
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///vehical_detections.db')

print(f"[INFO] Connecting to database: {DATABASE_URL}")

try:
    # Create engine
    engine = create_engine(DATABASE_URL)
    
    # Create all tables (including users table)
    Base.metadata.create_all(bind=engine)
    
    print("[SUCCESS] Database tables created successfully!")
    print("[INFO] Users table is now ready for authentication")
except Exception as e:
    print(f"[ERROR] Failed to create tables: {e}")
    import traceback
    traceback.print_exc()
