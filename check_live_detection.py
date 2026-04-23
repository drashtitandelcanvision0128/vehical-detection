import sqlite3

conn = sqlite3.connect('vehical_detections.db')
cursor = conn.cursor()

cursor.execute('SELECT report_id, detection_type, video_path, image_data, vehicle_count FROM detection_history WHERE detection_type = "live" ORDER BY timestamp DESC LIMIT 3')
rows = cursor.fetchall()
for r in rows:
    print(f'ID: {r[0]}, Type: {r[1]}, Video: {r[2]}, Image: {"Yes" if r[3] else "No"}, Count: {r[4]}')

conn.close()
