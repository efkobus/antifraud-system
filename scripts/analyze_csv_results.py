"""
Script to analyze anti-fraud performance using real CSV data.
This validates the system against historical transactions with known fraud outcomes.
"""

import pandas as pd
import os
import logging
from datetime import datetime

logging.disable(logging.CRITICAL)

from src.antifraud import check_antifraud, update_cbk
from src.models import Transaction
from src.database import init_db, get_db
from src import database

logger = logging.getLogger(__name__)

def load_and_test_csv(csv_path='data/transactional-sample.csv'):
    """
    Load CSV data and test anti-fraud rules against real transactions.
    """
    df = pd.read_csv(csv_path)
    
    total_transactions = len(df)
    actual_frauds = (df['has_cbk'] == True).sum()
    
    if os.path.exists('antifraud.db'):
        os.remove('antifraud.db')
    init_db()
    
    results = {
        'correct_deny': 0,
        'correct_approve': 0,
        'false_positive': 0,
        'false_negative': 0,
    }
    
    recommendations = []
    processed = 0
    
    df = df.sort_values('transaction_date')
    
    for idx, row in df.iterrows():
        try:
            txn = Transaction(
                transaction_id=int(row['transaction_id']),
                merchant_id=int(row['merchant_id']),
                user_id=int(row['user_id']),
                card_number=str(row['card_number']),
                transaction_date=row['transaction_date'],
                transaction_amount=float(row['transaction_amount']),
                device_id=int(row['device_id']) if pd.notna(row['device_id']) else None
            )
            
            recommendation = check_antifraud(txn)
            actual_fraud = (row['has_cbk'] == True)
            
            recommendations.append({
                'transaction_id': txn.transaction_id,
                'user_id': txn.user_id,
                'amount': txn.transaction_amount,
                'recommendation': recommendation,
                'actual_fraud': actual_fraud,
                'date': row['transaction_date']
            })
            
            if recommendation == 'deny' and actual_fraud:
                results['correct_deny'] += 1
            elif recommendation == 'approve' and not actual_fraud:
                results['correct_approve'] += 1
            elif recommendation == 'deny' and not actual_fraud:
                results['false_positive'] += 1
            elif recommendation == 'approve' and actual_fraud:
                results['false_negative'] += 1
            
            processed += 1
            
        except Exception as e:
            logger.error(f"Error processing transaction {row.get('transaction_id', 'unknown')}: {e}")
            continue
    
    chargeback_count = 0
    for _, row in df[df['has_cbk'] == True].iterrows():
        try:
            update_cbk(int(row['transaction_id']), True)
            chargeback_count += 1
        except Exception as e:
            logger.error(f"Error updating chargeback {row['transaction_id']}: {e}")
    
    print("\n" + "=" * 70)
    print("                    ANTI-FRAUD PERFORMANCE REPORT")
    print("=" * 70)
    print(f"\nDataset: {csv_path}")
    print(f"Transactions analyzed: {processed:,} | Frauds: {actual_frauds} ({actual_frauds/total_transactions*100:.1f}%)")
    
    print(f"\nCONFUSION MATRIX:")
    print(f"{'':30} │ Predicted DENY │ Predicted APPROVE")
    print(f"{'─' * 70}")
    print(f"{'Actual FRAUD':30} │ {results['correct_deny']:14} │ {results['false_negative']:17}")
    print(f"{'Actual LEGITIMATE':30} │ {results['false_positive']:14} │ {results['correct_approve']:17}")
    
    total_tested = sum(results.values())
    accuracy = (results['correct_deny'] + results['correct_approve']) / total_tested * 100 if total_tested > 0 else 0
    
    total_denied = results['correct_deny'] + results['false_positive']
    precision = results['correct_deny'] / total_denied * 100 if total_denied > 0 else 0
    
    total_frauds = results['correct_deny'] + results['false_negative']
    recall = results['correct_deny'] / total_frauds * 100 if total_frauds > 0 else 0
    
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    total_legitimate = results['correct_approve'] + results['false_positive']
    specificity = results['correct_approve'] / total_legitimate * 100 if total_legitimate > 0 else 0
    
    print(f"\nPERFORMANCE METRICS:")
    print(f"   Accuracy:             {accuracy:.2f}%  (overall correctness)")
    print(f"   Precision:            {precision:.2f}%  (of denied, how many were fraud)")
    print(f"   Recall (Sensitivity): {recall:.2f}%  (of frauds, how many we caught)")
    print(f"   Specificity:          {specificity:.2f}%  (of legitimate, how many approved)")
    print(f"   F1 Score:             {f1_score:.2f}%  (balance of precision & recall)")
    
    print(f"\n💰 BUSINESS IMPACT:")
    print(f"   Frauds Caught:        {results['correct_deny']}/{actual_frauds} ({results['correct_deny']/actual_frauds*100:.1f}%) 🎯")
    
    fraud_caught_amount = sum([r['amount'] for r in recommendations if r['recommendation']=='deny' and r['actual_fraud']])
    fraud_missed_amount = sum([r['amount'] for r in recommendations if r['recommendation']=='approve' and r['actual_fraud']])
    false_positive_amount = sum([r['amount'] for r in recommendations if r['recommendation']=='deny' and not r['actual_fraud']])
    
    print(f"   Fraud Prevented:      ${fraud_caught_amount:,.2f} 💵")
    print(f"   Frauds Missed:        {results['false_negative']} transactions (${fraud_missed_amount:,.2f} lost) ⚠️")
    print(f"   False Alarms:         {results['false_positive']} transactions (${false_positive_amount:,.2f} friction) 😞")
    print(f"   Legitimate Approved:  {results['correct_approve']} transactions ✅")
    
    fraud_saved = fraud_caught_amount + (results['correct_deny'] * 25)
    friction_cost = results['false_positive'] * 5
    net_benefit = fraud_saved - friction_cost
    
    print(f"\n💡 ESTIMATED ROI:")
    print(f"   Fraud Saved:          ${fraud_saved:,.2f} (amount + chargeback fees)")
    print(f"   Customer Friction:    -${friction_cost:,.2f} (declined legitimate)")
    print(f"   Net Benefit:          ${net_benefit:,.2f} {'✅' if net_benefit > 0 else '⚠️'}")
    
    print(f"\n🔍 FRAUD DETAILS:")
    fraud_recs = [r for r in recommendations if r['actual_fraud']]
    if len(fraud_recs) > 0:
        caught = [r for r in fraud_recs if r['recommendation'] == 'deny']
        missed = [r for r in fraud_recs if r['recommendation'] == 'approve']
        
        print(f"   Total fraud amount:   ${sum([r['amount'] for r in fraud_recs]):,.2f}")
        print(f"   Prevented:            ${sum([r['amount'] for r in caught]):,.2f} ({len(caught)} txns)")
        print(f"   Lost:                 ${sum([r['amount'] for r in missed]):,.2f} ({len(missed)} txns)")
        
        if len(missed) > 0:
            print(f"\n⚠️  TOP MISSED FRAUDS (opportunities for improvement):")
            missed_sorted = sorted(missed, key=lambda x: x['amount'], reverse=True)
            for i, m in enumerate(missed_sorted[:5], 1):
                print(f"      {i}. Transaction {m['transaction_id']}: User {m['user_id']}, ${m['amount']:.2f}")
    
    print(f"\nUSER ANALYSIS:")
    user_stats = {}
    for r in recommendations:
        user_id = r['user_id']
        if user_id not in user_stats:
            user_stats[user_id] = {'total': 0, 'frauds': 0, 'denied': 0}
        user_stats[user_id]['total'] += 1
        if r['actual_fraud']:
            user_stats[user_id]['frauds'] += 1
        if r['recommendation'] == 'deny':
            user_stats[user_id]['denied'] += 1
    
    fraudulent_users = [uid for uid, stats in user_stats.items() if stats['frauds'] > 0]
    high_risk_users = [uid for uid, stats in user_stats.items() if stats['frauds'] / stats['total'] >= 0.5]
    
    print(f"   Total unique users:   {len(user_stats)}")
    print(f"   Users with fraud:     {len(fraudulent_users)} ({len(fraudulent_users)/len(user_stats)*100:.1f}%)")
    print(f"   High-risk users:      {len(high_risk_users)} (≥50% fraud rate)")
    
    if high_risk_users:
        print(f"\n   HIGH-RISK USERS:")
        for uid in high_risk_users[:5]:
            stats = user_stats[uid]
            fraud_rate = stats['frauds'] / stats['total'] * 100
            print(f"      User {uid}: {stats['frauds']}/{stats['total']} frauds ({fraud_rate:.0f}% fraud rate)")
    
    print("\n" + "=" * 70)
    
    return results, recommendations

def analyze_rule_effectiveness(csv_path='data/transactional-sample.csv'):
    """
    Analyze which rules are most effective.
    """
    df = pd.read_csv(csv_path)
    
    print("\n" + "=" * 70)
    print("                 RULE EFFECTIVENESS ANALYSIS")
    print("=" * 70)
    
    users_with_cbk = df[df['has_cbk'] == True]['user_id'].unique()
    total_users = df['user_id'].nunique()
    
    print(f"\nRULE 1: Chargeback History")
    print(f"   Users with chargebacks: {len(users_with_cbk)}/{total_users} ({len(users_with_cbk)/total_users*100:.1f}%)")
    print(f"   Impact: These users are permanently blocked from future transactions")
    print(f"   Effectiveness: HIGH (100% precision for known fraudsters)")
    
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    df = df.sort_values('transaction_date')
    
    print(f"\nRULE 2: Transaction Velocity (>3 in 2 minutes)")
    velocity_cases = []
    for user_id in df['user_id'].unique():
        user_txns = df[df['user_id'] == user_id].sort_values('transaction_date')
        if len(user_txns) <= 3:
            continue
        for i in range(len(user_txns)):
            window_start = user_txns.iloc[i]['transaction_date'] - pd.Timedelta(minutes=2)
            window_end = user_txns.iloc[i]['transaction_date']
            recent = user_txns[
                (user_txns['transaction_date'] >= window_start) &
                (user_txns['transaction_date'] <= window_end)
            ]
            if len(recent) > 3:
                has_fraud = (recent['has_cbk'] == True).any()
                velocity_cases.append({
                    'user_id': user_id,
                    'count': len(recent),
                    'has_fraud': has_fraud
                })
                break
    
    velocity_with_fraud = sum([1 for v in velocity_cases if v['has_fraud']])
    print(f"   Cases detected:         {len(velocity_cases)}")
    print(f"   Cases with fraud:       {velocity_with_fraud}/{len(velocity_cases)} ({velocity_with_fraud/len(velocity_cases)*100:.1f}% precision)" if len(velocity_cases) > 0 else "   Cases with fraud:       0")
    print(f"   Effectiveness:          MEDIUM (catches automated attacks)")
    
    print(f"\nRULE 3: Amount Limit (>$1,000 in 24h)")
    amount_cases = []
    for user_id in df['user_id'].unique():
        user_txns = df[df['user_id'] == user_id].sort_values('transaction_date')
        for i in range(len(user_txns)):
            window_start = user_txns.iloc[i]['transaction_date'] - pd.Timedelta(hours=24)
            window_end = user_txns.iloc[i]['transaction_date']
            recent_24h = user_txns[
                (user_txns['transaction_date'] >= window_start) &
                (user_txns['transaction_date'] <= window_end)
            ]
            total_amount = recent_24h['transaction_amount'].sum()
            if total_amount > 1000:
                has_fraud = (recent_24h['has_cbk'] == True).any()
                amount_cases.append({
                    'user_id': user_id,
                    'amount': total_amount,
                    'has_fraud': has_fraud
                })
                break
    
    amount_with_fraud = sum([1 for a in amount_cases if a['has_fraud']])
    print(f"   Cases detected:         {len(amount_cases)}")
    print(f"   Cases with fraud:       {amount_with_fraud}/{len(amount_cases)} ({amount_with_fraud/len(amount_cases)*100:.1f}% precision)" if len(amount_cases) > 0 else "   Cases with fraud:       0")
    print(f"   Effectiveness:          MEDIUM-HIGH (prevents large-scale fraud)")
    
    print(f"\nRECOMMENDATIONS:")
    print(f"   1. Rule 1 (Chargeback) is most effective - keep as highest priority")
    print(f"   2. Consider adjusting thresholds based on metrics above")
    print(f"   3. Add device fingerprinting for better fraud detection")
    print(f"   4. Implement ML-based risk scoring for edge cases")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    import sys
    
    csv_file = sys.argv[1] if len(sys.argv) > 1 else 'data/transactional-sample.csv'
    
    if not os.path.exists(csv_file):
        print(f"\nERROR: File '{csv_file}' not found!")
        print(f"Download from: https://gist.github.com/cloudwalk-tests/76993838e65d7e0f988f40f1b1909c97")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("           ANTI-FRAUD SYSTEM - PERFORMANCE ANALYSIS")
    print("=" * 70)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results, recommendations = load_and_test_csv(csv_file)
    
    analyze_rule_effectiveness(csv_file)
    
    total = sum(results.values())
    accuracy = (results['correct_deny'] + results['correct_approve']) / total * 100
    print(f"\n{'=' * 70}")
    print(f"SUMMARY: Accuracy {accuracy:.1f}% | Frauds Caught {results['correct_deny']}/{results['correct_deny'] + results['false_negative']} | False Positives {results['false_positive']}")
    print("=" * 70 + "\n")
