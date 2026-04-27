"""
Direct SQL fix to add missing columns to users table.
Run this locally to fix the database schema.
"""
import psycopg2
from sqlalchemy import create_engine, text

# Database connection from .env (local database used by Flask app)
DB_URL = "postgresql://postgres:admin@localhost:5432/vehical_detections"

def fix_columns():
    engine = create_engine(DB_URL)
    
    with engine.connect() as conn:
        # Check existing columns
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='users'"))
        existing = {row[0] for row in result.fetchall()}
        print(f"Existing columns: {sorted(existing)}")
        
        # Add missing columns
        if 'theme' not in existing:
            print("Adding 'theme' column...")
            conn.execute(text("ALTER TABLE users ADD COLUMN theme VARCHAR(10) DEFAULT 'light'"))
            conn.commit()
        else:
            print("'theme' column already exists")
        
        if 'reset_token' not in existing:
            print("Adding 'reset_token' column...")
            conn.execute(text("ALTER TABLE users ADD COLUMN reset_token VARCHAR(255)"))
            conn.commit()
        else:
            print("'reset_token' column already exists")
        
        if 'reset_token_expires' not in existing:
            print("Adding 'reset_token_expires' column...")
            conn.execute(text("ALTER TABLE users ADD COLUMN reset_token_expires TIMESTAMP"))
            conn.commit()
        else:
            print("'reset_token_expires' column already exists")
        
        print("\nDone! Database schema updated.")

if __name__ == "__main__":
    fix_columns()
