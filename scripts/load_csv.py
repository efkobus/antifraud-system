"""
Script to load historical data from CSV into the database.
"""

import pandas as pd
from src.database import get_db, init_db
from src.antifraud import update_cbk
from src.models import hash_card
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

init_db()

logger.info("Loading data from CSV...")
df = pd.read_csv('data/transactional-sample.csv')

logger.info(f"Total transactions in CSV: {len(df)}")

with get_db() as conn:
    cur = conn.cursor()
    
    transactions_loaded = 0
    for _, row in df.iterrows():
        try:
            card_hash = hash_card(str(row['card_number']))
            
            has_cbk = row['has_cbk'] == 'TRUE'
            
            cur.execute("""
                INSERT OR IGNORE INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                int(row['transaction_id']),
                int(row['merchant_id']),
                int(row['user_id']),
                card_hash,
                str(row['transaction_date']),
                float(row['transaction_amount']),
                int(row['device_id']) if pd.notna(row['device_id']) else None,
                has_cbk
            ))
            
            cur.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (int(row['user_id']),))
            
            transactions_loaded += 1
            
        except Exception as e:
            logger.error(f"Error loading transaction {row['transaction_id']}: {e}")
            continue
    
    conn.commit()
    logger.info(f"{transactions_loaded} transactions loaded into database")

logger.info("Processing chargebacks...")
chargebacks_found = 0

for _, row in df.iterrows():
    if row['has_cbk'] == 'TRUE':
        try:
            update_cbk(int(row['transaction_id']), True)
            chargebacks_found += 1
        except Exception as e:
            logger.error(f"Error updating chargeback {row['transaction_id']}: {e}")

logger.info(f"{chargebacks_found} chargebacks processed")
logger.info("Data load completed successfully!")
