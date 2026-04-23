from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///vehical_detections.db')
engine = create_engine(DATABASE_URL)
conn = engine.connect()

result = conn.execute(text('SELECT report_id, detection_type, image_data IS NOT NULL as has_image, vehicle_count FROM detection_history ORDER BY timestamp DESC LIMIT 5'))
print('Recent history entries:')
for row in result:
    print(f'ID: {row[0]}, Type: {row[1]}, Has Image: {row[2]}, Vehicles: {row[3]}')

conn.close()
