import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///vehical_detections.db')
engine = create_engine(DATABASE_URL)
conn = engine.connect()

# Get all tables
if 'postgresql' in DATABASE_URL:
    result = conn.execute(text("""
        SELECT tablename FROM pg_tables 
        WHERE schemaname = 'public'
    """))
    tables = [(row[0],) for row in result]
else:
    result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
    tables = [(row[0],) for row in result]

print('Tables:', tables)

# Check live_detections table
if ('live_detections',) in tables:
    result = conn.execute(text('SELECT * FROM live_detections'))
    detections = result.fetchall()
    print(f'Live detections count: {len(detections)}')
    for det in detections:
        print(f'ID: {det[0]}, Report ID: {det[1]}, Vehicles: {det[6]}, Timestamp: {det[3]}, Breakdown: {det[9]}')
else:
    print('live_detections table does not exist')

# Check all tables data
for table in tables:
    table_name = table[0]
    result = conn.execute(text(f'SELECT COUNT(*) FROM {table_name}'))
    count = result.fetchone()[0]
    print(f'{table_name}: {count} rows')

conn.close()
