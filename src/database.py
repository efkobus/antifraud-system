import sqlite3
from contextlib import contextmanager

DB_FILE = 'antifraud.db'

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_FILE)
    try:
        yield conn
    finally:
        conn.close()

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
        
        cur.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON transactions(user_id)')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_transaction_date ON transactions(transaction_date)')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_user_date ON transactions(user_id, transaction_date)')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_card_hash ON transactions(card_number)')
        
        conn.commit()
