# main.py
from fastapi import FastAPI
from models import Transaction, Recommendation
from antifraud import check_antifraud
from database import init_db

app = FastAPI()
init_db()

@app.post("/antifraud", response_model=Recommendation)
def antifraud(txn: Transaction):
    recommendation = check_antifraud(txn)
    return {"transaction_id": txn.transaction_id, "recommendation": recommendation}
