from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:admin@localhost:5432/vehical_detections')

with engine.connect() as conn:
    try:
        conn.execute(text('ALTER TABLE number_plate_detections ALTER COLUMN region TYPE VARCHAR(50);'))
        conn.commit()
        print('Region column increased to VARCHAR(50) successfully')
    except Exception as e:
        print(f'Error: {e}')
        conn.rollback()
