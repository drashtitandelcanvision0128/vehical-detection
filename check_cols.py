import psycopg2
conn = psycopg2.connect('postgresql://postgres:admin@localhost:5432/vehical_detections')
cur = conn.cursor()
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='users' ORDER BY ordinal_position")
print("Users columns:", [r[0] for r in cur.fetchall()])
conn.close()
