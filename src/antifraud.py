from datetime import datetime, timedelta
from src.database import get_db
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

MAX_TRANSACTIONS_IN_2MIN = 3
MAX_AMOUNT_IN_24H = 1000.0

def check_antifraud(txn):
    """
    Check if a transaction should be approved or denied based on anti-fraud rules.
    
    Rules:
    1. Deny if user had prior chargeback
    2. Deny if >3 transactions in 2 minutes
    3. Deny if sum of last 24h + current transaction > $1000
    """
    logger.info(f"Processing transaction {txn.transaction_id} for user {txn.user_id}")
    
    try:
        dt = datetime.fromisoformat(txn.transaction_date)
    except ValueError:
        logger.error(f"DENIED: Invalid date for transaction {txn.transaction_id}")
        return 'deny'
    
    card_hash = txn.get_card_hash()
    
    with get_db() as conn:
        cur = conn.cursor()
        
        # Rule 1: Check prior chargeback
        cur.execute("SELECT has_prior_cbk FROM users WHERE user_id = ?", (txn.user_id,))
        prior_cbk = cur.fetchone()
        if prior_cbk and prior_cbk[0]:
            logger.warning(f"DENIED: User {txn.user_id} has prior chargeback (transaction {txn.transaction_id})")
            return 'deny'
        
        # Rule 2: Check too many in row (>=3 in 2 min, so 4th would be denied)
        recent_time = dt - timedelta(minutes=2)
        cur.execute("""
            SELECT COUNT(*) FROM transactions
            WHERE user_id = ? AND datetime(transaction_date) > datetime(?)
        """, (txn.user_id, recent_time.isoformat()))
        count_recent = cur.fetchone()[0]

        if count_recent >= MAX_TRANSACTIONS_IN_2MIN:
            logger.warning(
                f"DENIED: User {txn.user_id} exceeded transaction limit "
                f"({count_recent} transactions in 2 minutes, attempting {count_recent + 1}) - transaction {txn.transaction_id}"
            )
            return 'deny'
        
        # Rule 3: Check amount in period (>1000 in 24h)
        day_ago = dt - timedelta(hours=24)
        cur.execute("""
            SELECT SUM(transaction_amount) FROM transactions
            WHERE user_id = ? AND datetime(transaction_date) > ?
        """, (txn.user_id, day_ago.isoformat()))
        total_day = cur.fetchone()[0] or 0
        if total_day + txn.transaction_amount > MAX_AMOUNT_IN_24H:
            logger.warning(
                f"DENIED: User {txn.user_id} exceeded amount limit "
                f"(${total_day:.2f} + ${txn.transaction_amount:.2f} > ${MAX_AMOUNT_IN_24H}) "
                f"- transaction {txn.transaction_id}"
            )
            return 'deny'
        
        try:
            cur.execute("""
                INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (txn.transaction_id, txn.merchant_id, txn.user_id, card_hash,
                  txn.transaction_date, txn.transaction_amount, txn.device_id, False))
            
            cur.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (txn.user_id,))
            conn.commit()
            
            logger.info(
                f"APPROVED: Transaction {txn.transaction_id} for user {txn.user_id} "
                f"- ${txn.transaction_amount:.2f}"
            )
        except Exception as e:
            logger.error(f"Error storing transaction {txn.transaction_id}: {e}")
            return 'deny'
    
    return 'approve'

def update_cbk(transaction_id, has_cbk):
    """
    Update chargeback status of a transaction.
    This function is called days after approval when a chargeback is identified.
    """
    logger.info(f"Updating chargeback for transaction {transaction_id}: {has_cbk}")
    
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE transactions SET has_cbk = ? WHERE transaction_id = ?", (has_cbk, transaction_id))
        
        if has_cbk:
            cur.execute("""
                UPDATE users SET has_prior_cbk = TRUE
                WHERE user_id = (SELECT user_id FROM transactions WHERE transaction_id = ?)
            """, (transaction_id,))
            
            cur.execute("SELECT user_id FROM transactions WHERE transaction_id = ?", (transaction_id,))
            result = cur.fetchone()
            if result:
                logger.warning(f"Chargeback confirmed for transaction {transaction_id} - User {result[0]} marked")
        
        conn.commit()
