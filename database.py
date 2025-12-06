import sqlite3
from contextlib import contextmanger

DB_FILE = 'antifraud.db'

@contextmanger
def get_db():
    conn = sqlite3.connect(DB_FILE)
    try:
        yild conn
    finally:
        conn_close()

def init_db():
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INTEGER PRIMARY KEY,
                merchant_id INTEGER,
                user_id INTEGER,
                card_number TEXT,
                transaction_date TEXT,
                transaction_amount REAL,
                device_id INTEGER,
                has_cbk BOOLEAN DEFAULT FALSE
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                has_prior_cbk BOOLEAN DEFAULT FALSE
            )
        ''')
        conn.commit()
