import pandas as pd
from database import get_db
from antifraud import update_cbk

df = pd.read_csv('transactional-sample.csv')
with get_db() as conn:
    cur = conn.cursor()
    for _, row in df.iterrows():
        cur.execute("""
            INSERT OR IGNORE INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, tuple(row))
    conn.commit()

# Simulate updating cbk from CSV
for _, row in df.iterrows():
    if row['has_cbk'] == 'TRUE':
        update_cbk(row['transaction_id'], True)
