import psycopg2
conn = psycopg2.connect('postgresql://postgres:admin@localhost:5432/vehical_detections')
conn.autocommit = True
cur = conn.cursor()

# Add missing columns to users
missing = {
    'users': ['role', 'two_factor_enabled', 'two_factor_secret']
}

# Check existing columns
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='users'")
existing = {r[0] for r in cur.fetchall()}
print("Existing users columns:", existing)

if 'role' not in existing:
    cur.execute("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user'")
    print("Added role column")

if 'two_factor_enabled' not in existing:
    cur.execute("ALTER TABLE users ADD COLUMN two_factor_enabled INTEGER DEFAULT 0")
    print("Added two_factor_enabled column")

if 'two_factor_secret' not in existing:
    cur.execute("ALTER TABLE users ADD COLUMN two_factor_secret VARCHAR(255)")
    print("Added two_factor_secret column")

# Add geolocation to detection tables
for table in ['image_detections', 'video_detections', 'live_detections']:
    cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}'")
    existing = {r[0] for r in cur.fetchall()}
    
    if 'latitude' not in existing:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN latitude FLOAT")
        print(f"Added latitude to {table}")
    
    if 'longitude' not in existing:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN longitude FLOAT")
        print(f"Added longitude to {table}")

# Verify
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='users' ORDER BY ordinal_position")
print("\nFinal users columns:", [r[0] for r in cur.fetchall()])

conn.close()
print("Done!")
