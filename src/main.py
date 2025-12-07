# main.py
from fastapi import FastAPI, HTTPException
from src.models import Transaction, Recommendation
from src.antifraud import check_antifraud
from src.database import init_db
from src.settings import settings
import logging

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="Anti-fraud system for real-time suspicious transaction detection",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Initialize database
init_db()
logger.info(f"API {settings.api_title} v{settings.api_version} started")

@app.get("/")
def root():
    """Root endpoint with API information"""
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "status": "online",
        "endpoints": {
            "antifraud": "/antifraud",
            "docs": "/docs",
            "health": "/health"
        }
    }

@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/antifraud", response_model=Recommendation)
def antifraud(txn: Transaction):
    """
    Analyze a transaction and return recommendation (approve/deny).
    
    Rules applied:
    - Deny if user has chargeback history
    - Deny if >3 transactions in 2 minutes
    - Deny if total amount in last 24h exceeds R$1,000
    """
    try:
        recommendation = check_antifraud(txn)
        return {"transaction_id": txn.transaction_id, "recommendation": recommendation}
    except Exception as e:
        logger.error(f"Error processing transaction {txn.transaction_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal error processing transaction")
