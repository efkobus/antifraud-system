# Anti-Fraud API 🛡️

This system analyzes transactions in real-time and decides whether they should be approved or denied based on fraud detection rules.

## 📋 Features

- **RESTful API** with FastAPI
- **Robust validation** with Pydantic
- **PCI-DSS Security** - card numbers are hashed (SHA-256)
- **Optimized performance** with database indexes
- **Complete logging** of all decisions
- **Comprehensive unit tests**
- **Configurable settings** via `.env` file

## 🚀 Installation

### Prerequisites

- Python 3.10+
- pip

### Steps

1. Clone the repository:
```bash
git clone <repository-url>
cd antifraud-challenge
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Download sample data (optional, for testing):
```bash
wget -O data/transactional-sample.csv "https://gist.githubusercontent.com/cloudwalk-tests/76993838e65d7e0f988f40f1b1909c97/raw/b236c0e375f8f7769c8e5914b6bb88d08b1c563d/transactional-sample.csv"
```

5. (Optional) Configure environment variables:
```bash
cp .env.example .env
# Edit .env file as needed
```

## 🏃 Running

### Start the API

```bash
uvicorn src.main:app --reload
```

The API will be available at: `http://localhost:8000`

Interactive documentation (Swagger): `http://localhost:8000/docs`

### Request Example

```bash
curl -X POST http://localhost:8000/antifraud \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": 123456,
    "merchant_id": 29744,
    "user_id": 97051,
    "card_number": "434505******9116",
    "transaction_date": "2024-12-06T10:30:00",
    "transaction_amount": 150.50,
    "device_id": 285475
  }'
```

### Response Example

```json
{
  "transaction_id": 123456,
  "recommendation": "approve"
}
```

## 🔒 Anti-Fraud Rules

The system implements the following rules:

### 1. Chargeback History
- **Action**: Deny transaction
- **Condition**: User has prior chargeback history
- **Reason**: Users with fraud history have high probability of recurrence

### 2. Transaction Sequence Limit
- **Action**: Deny transaction
- **Condition**: More than 3 transactions in 2 minutes
- **Reason**: Typical pattern of automated fraud or card cloning
- **Configurable**: `MAX_TRANSACTIONS_IN_2MIN=3`

### 3. Amount Limit per Period
- **Action**: Deny transaction
- **Condition**: Sum of transactions in last 24h + current transaction > $1,000
- **Reason**: Prevents high-value fraud
- **Configurable**: `MAX_AMOUNT_IN_24H=1000.0`

## 🧪 Tests

Run unit tests:

```bash
pytest test_antifraud.py -v
```

Test coverage:

```bash
pytest test_antifraud.py --cov=. --cov-report=html
```

### Included Test Cases

- ✅ Normal transaction approval
- ✅ Denial for high amount in 24h
- ✅ Denial for many transactions in sequence
- ✅ Denial for prior chargeback
- ✅ Invalid card number validation
- ✅ Date format validation
- ✅ Negative amount validation
- ✅ Transactions after time window

## 📁 Project Structure

```
antifraud-challenge/
├── src/                      # Source code
│   ├── main.py              # FastAPI application
│   ├── models.py            # Pydantic models
│   ├── antifraud.py         # Business logic
│   ├── database.py          # Database layer
│   └── settings.py          # Configuration
├── tests/                    # Unit tests
│   └── test_antifraud.py
├── scripts/                  # Utility scripts
│   ├── analyze_csv_results.py  # Performance analysis
│   ├── load_csv.py             # Load historical data
│   └── run_csv_analysis.sh     # Run analysis script
├── data/                     # Data files (gitignored)
│   └── transactional-sample.csv
├── .env.example             # Environment variables template
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🔧 Configuration

The following settings can be adjusted via environment variables (`.env` file):

```bash
# Database
DB_FILE=antifraud.db

# Anti-fraud rules
MAX_TRANSACTIONS_PER_2MIN=3
MAX_AMOUNT_PER_24H=1000.0
MAX_TRANSACTION_AMOUNT=1000000.0

# API
API_HOST=0.0.0.0
API_PORT=8000

# Logging
LOG_LEVEL=INFO
```

## 🔐 Security

### PCI-DSS Compliance

- **Does not store complete card numbers**: Only SHA-256 hash is stored
- **Input validation**: All fields are validated before processing
- **Secure logging**: Card numbers do not appear in logs

### Implemented Best Practices

1. ✅ Hash of sensitive data (card numbers)
2. ✅ Strict input validation
3. ✅ Database indexes for performance
4. ✅ Logging of all decisions
5. ✅ Error handling
6. ✅ Automated tests

## 📊 Performance

### Optimizations

- **Database indexes**:
  - `idx_user_id` - Queries by user
  - `idx_transaction_date` - Queries by period
  - `idx_user_date` - Composite queries (user + period)
  - `idx_card_hash` - Queries by card

- **Expected latency**: < 50ms per transaction (under normal conditions)

## 🚦 How the System Works

1. **Reception**: API receives JSON payload with transaction data
2. **Validation**: Pydantic validates format and data types
3. **Analysis**: System checks the 3 anti-fraud rules in sequence
4. **Decision**: Returns "approve" or "deny"
5. **Storage**: If approved, transaction is stored (with card hash)
6. **Logging**: All decisions are logged

### Chargeback Flow

1. Transaction is initially **approved**
2. Days later, chargeback is identified
3. `/update_cbk` endpoint (internal) is called
4. User is marked with `has_prior_cbk = TRUE`
5. Future transactions from user are **automatically denied**

## 📝 API Endpoints

### POST `/antifraud`

Analyzes a transaction and returns recommendation.

**Request:**
```json
{
  "transaction_id": 2342357,
  "merchant_id": 29744,
  "user_id": 97051,
  "card_number": "434505******9116",
  "transaction_date": "2019-11-31T23:16:32.812632",
  "transaction_amount": 373,
  "device_id": 285475
}
```

**Response:**
```json
{
  "transaction_id": 2342357,
  "recommendation": "approve"
}
```

## 👤 Author

Eduardo Kobus