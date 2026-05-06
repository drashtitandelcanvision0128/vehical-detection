
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:admin@localhost:5432/vehical_detections')

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

try:
    from sqlalchemy import text
    result = session.execute(text("SELECT task_id, interval_seconds, source, task_type, enabled, last_run, next_run FROM scheduled_tasks"))
    tasks = result.fetchall()
    print(f"Found {len(tasks)} tasks in database:")
    for task in tasks:
        print(f"ID: {task[0]}, Interval: {task[1]}s, Source: {task[2]}, Type: {task[3]}, Enabled: {task[4]}")
        print(f"  Last Run: {task[5]}")
        print(f"  Next Run: {task[6]}")
except Exception as e:
    print(f"Error: {e}")
finally:
    session.close()
