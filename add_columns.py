from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:admin@localhost:5432/vehical_detections')

with engine.connect() as conn:
    try:
        conn.execute(text('ALTER TABLE number_plate_detections ADD COLUMN IF NOT EXISTS region VARCHAR(10);'))
        conn.execute(text('ALTER TABLE number_plate_detections ADD COLUMN IF NOT EXISTS plate_image TEXT;'))
        conn.commit()
        print('Columns added successfully')
    except Exception as e:
        print(f'Error: {e}')
        conn.rollback()
