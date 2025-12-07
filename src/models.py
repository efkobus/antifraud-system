from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import hashlib
import re

def hash_card(card_number: str) -> str:
    """Hash card number for PCI-DSS security"""
    return hashlib.sha256(card_number.encode()).hexdigest()

class Transaction(BaseModel):
    transaction_id: int = Field(..., gt=0, description="Unique transaction ID")
    merchant_id: int = Field(..., gt=0, description="Merchant ID")
    user_id: int = Field(..., gt=0, description="User ID")
    card_number: str = Field(..., min_length=16, max_length=19, description="Card number (can be masked)")
    transaction_date: str = Field(..., description="Transaction date in ISO format")
    transaction_amount: float = Field(..., gt=0, description="Transaction amount")
    device_id: int | None = Field(None, description="Device ID")
    
    @field_validator('card_number')
    @classmethod
    def validate_card_format(cls, v: str) -> str:
        """Validate card format (accepts masked with *)"""
        if not v:
            raise ValueError('Card number cannot be empty')
        
        clean_number = v.replace('*', '').replace(' ', '')
        
        if len(clean_number) < 10:
            raise ValueError('Invalid card format')
        
        if '*' not in v and not clean_number.isdigit():
            raise ValueError('Card number must contain only digits')
        
        return v
    
    @field_validator('transaction_date')
    @classmethod
    def validate_date(cls, v: str) -> str:
        """Validate ISO date format"""
        try:
            datetime.fromisoformat(v)
        except ValueError:
            raise ValueError('Date must be in ISO format (YYYY-MM-DDTHH:MM:SS)')
        return v
    
    @field_validator('transaction_amount')
    @classmethod
    def validate_amount(cls, v: float) -> float:
        """Validate that amount is positive and reasonable"""
        if v <= 0:
            raise ValueError('Transaction amount must be positive')
        if v > 1000000:
            raise ValueError('Transaction amount exceeds maximum limit')
        return round(v, 2)
    
    def get_card_hash(self) -> str:
        """Return hash of card number"""
        return hash_card(self.card_number)

class Recommendation(BaseModel):
    transaction_id: int
    recommendation: str = Field(..., pattern="^(approve|deny)$")
