"""
Unit tests for the anti-fraud system.
"""

import pytest
import os
from datetime import datetime, timedelta

import sys
from src import database
TEST_DB = 'test_antifraud.db'
database.DB_FILE = TEST_DB

try:
    from src import settings
    settings.settings.db_file = TEST_DB
except:
    pass

from fastapi.testclient import TestClient
from src.main import app
from src.database import init_db, get_db
from src.antifraud import update_cbk

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    """Setup and teardown test database"""
    database.DB_FILE = TEST_DB
    
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    
    init_db()
    
    yield
    
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_approve_normal_transaction():
    """Test approval of normal transaction"""
    response = client.post("/antifraud", json={
        "transaction_id": 9999999,
        "merchant_id": 12345,
        "user_id": 99999,
        "card_number": "434505******9116",
        "transaction_date": "2024-01-01T10:00:00",
        "transaction_amount": 100.0,
        "device_id": 12345
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["transaction_id"] == 9999999
    assert data["recommendation"] == "approve"

def test_deny_high_amount_in_24h():
    """Test denial for high amount in 24h"""
    user_id = 88888
    base_time = datetime.now()
    
    response1 = client.post("/antifraud", json={
        "transaction_id": 1000001,
        "merchant_id": 12345,
        "user_id": user_id,
        "card_number": "434505******9116",
        "transaction_date": base_time.isoformat(),
        "transaction_amount": 600.0,
        "device_id": 12345
    })
    assert response1.json()["recommendation"] == "approve"
    
    response2 = client.post("/antifraud", json={
        "transaction_id": 1000002,
        "merchant_id": 12345,
        "user_id": user_id,
        "card_number": "434505******9116",
        "transaction_date": (base_time + timedelta(hours=1)).isoformat(),
        "transaction_amount": 500.0,
        "device_id": 12345
    })
    assert response2.json()["recommendation"] == "deny"

def test_deny_many_transactions():
    """Test denial for many transactions in sequence"""
    user_id = 77777
    base_time = datetime.now()
    
    for i in range(3):
        response = client.post("/antifraud", json={
            "transaction_id": 2000000 + i,
            "merchant_id": 12345,
            "user_id": user_id,
            "card_number": "434505******9116",
            "transaction_date": (base_time + timedelta(seconds=i*20)).isoformat(),
            "transaction_amount": 50.0,
            "device_id": 12345
        })
        assert response.json()["recommendation"] == "approve"
    
    response4 = client.post("/antifraud", json={
        "transaction_id": 2000003,
        "merchant_id": 12345,
        "user_id": user_id,
        "card_number": "434505******9116",
        "transaction_date": (base_time + timedelta(seconds=70)).isoformat(),
        "transaction_amount": 50.0,
        "device_id": 12345
    })
    assert response4.json()["recommendation"] == "deny"

def test_deny_prior_chargeback():
    """Test denial for prior chargeback"""
    user_id = 66666
    base_time = datetime.now()
    
    response1 = client.post("/antifraud", json={
        "transaction_id": 3000001,
        "merchant_id": 12345,
        "user_id": user_id,
        "card_number": "434505******9116",
        "transaction_date": base_time.isoformat(),
        "transaction_amount": 100.0,
        "device_id": 12345
    })
    assert response1.json()["recommendation"] == "approve"
    
    # Simulate chargeback
    database.DB_FILE = TEST_DB
    update_cbk(3000001, True)
    
    response2 = client.post("/antifraud", json={
        "transaction_id": 3000002,
        "merchant_id": 12345,
        "user_id": user_id,
        "card_number": "434505******9116",
        "transaction_date": (base_time + timedelta(days=1)).isoformat(),
        "transaction_amount": 50.0,
        "device_id": 12345
    })
    assert response2.json()["recommendation"] == "deny"

def test_invalid_card_number():
    """Test validation of invalid card number"""
    response = client.post("/antifraud", json={
        "transaction_id": 4000001,
        "merchant_id": 12345,
        "user_id": 55555,
        "card_number": "123",  # Invalid
        "transaction_date": "2024-01-01T10:00:00",
        "transaction_amount": 100.0,
        "device_id": 12345
    })
    assert response.status_code == 422

def test_invalid_date_format():
    """Test validation of invalid date format"""
    response = client.post("/antifraud", json={
        "transaction_id": 4000002,
        "merchant_id": 12345,
        "user_id": 55555,
        "card_number": "434505******9116",
        "transaction_date": "invalid-date",
        "transaction_amount": 100.0,
        "device_id": 12345
    })
    assert response.status_code == 422

def test_negative_amount():
    """Test validation of negative amount"""
    response = client.post("/antifraud", json={
        "transaction_id": 4000003,
        "merchant_id": 12345,
        "user_id": 55555,
        "card_number": "434505******9116",
        "transaction_date": "2024-01-01T10:00:00",
        "transaction_amount": -100.0,
        "device_id": 12345
    })
    assert response.status_code == 422

def test_transactions_after_time_window():
    """Test that transactions outside time window are approved"""
    user_id = 44444
    base_time = datetime.now()
    
    for i in range(3):
        response = client.post("/antifraud", json={
            "transaction_id": 5000000 + i,
            "merchant_id": 12345,
            "user_id": user_id,
            "card_number": "434505******9116",
            "transaction_date": (base_time + timedelta(seconds=i*30)).isoformat(),
            "transaction_amount": 50.0,
            "device_id": 12345
        })
        assert response.json()["recommendation"] == "approve"
    
    response4 = client.post("/antifraud", json={
        "transaction_id": 5000003,
        "merchant_id": 12345,
        "user_id": user_id,
        "card_number": "434505******9116",
        "transaction_date": (base_time + timedelta(minutes=3)).isoformat(),
        "transaction_amount": 50.0,
        "device_id": 12345
    })
    assert response4.json()["recommendation"] == "approve"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
