from pydantic import BaseModel
from datetime import datetime

class Transaction(BaseModel):
    transaction_id: int
    merchant_id: int
    user_id: int
    card_number: str
    transaction_date: str
    transaction_amount: float
    device_id: int | None = None

class Recommendation(BaseModel):
    transaction_id: int
    recommendation: str
