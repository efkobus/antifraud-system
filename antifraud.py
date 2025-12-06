from datetime import datetime, timedelta
from database import get_db

def check_antifraud(txn):
    dt = datetime.fromisoformat(txn.transaction_date)

    with get_db() as conn:
        cur = conn.cursor()

        # Check prior chargeback
        cur.execute("SELECT has_prior_cbk FROM users WHERE user_id = ?", (txn.user_id,))
        has_prior_cbk = cur.fetchone()
        if prior_cbk and prior_cbk[0]:
            return 'deny'

        # Check too many in row ( >3 in 2 min)
        recent_time = dt - timedelta(minutes=2)
        cur.execute("""
            SELECT COUNT(*) FROM transactions
            WHERE user_id = ? AND datetime(transaction_date) > ?
        """, (txn.user_id, recent_time.isoformat()))
        count_recent = cur.fetchone()[0]
        if count_recent >= 3:
            return 'deny'
        
        # Check amount in period ( >1000 in 24h)
        day_ago = dt - timedelta(hours=24)
        cur.execute("""
            SELECT SUM(transaction_amount) FROM transactions
            WHERE user_id = ? AND datetime(transaction_date) > ?
        """, (txn.user_id, day_ago.isoformat()))
        total_day = cur.fetchone()[0] or 0
        if total_day + txn.transaction_amount > 1000:
            return 'deny'

        # If pass, store txn (assume approve, cbk updated later)
        cur.execute("""
            INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (txn.transaction_id, txn.merchant_id, txn.user_id, txn.card_number,
              txn.transaction_date, txn.transaction_amount, txn.device_id, False))

        cur.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (txn.user_id,))
        conn.commit()

    return 'approve'

def update_cbk(transaction_id, has_cbk):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE transactions SET has_cbk = ? WHERE transaction_id = ?", (has_cbk, transaction_id))
        if has_cbk:
            cur.execute("""
                UPDATE users SET has_prior_cbk = TRUE
                WHERE user_id = (SELECT user_id FROM transactions WHERE transaction_id = ?)
            """, (transaction_id,))
        conn.commit()
