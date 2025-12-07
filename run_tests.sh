#!/bin/bash

echo "Checking dependencies installation..."
source .venv/bin/activate 2>/dev/null || { echo "Virtual environment not found. Run: python3 -m venv .venv"; exit 1; }

echo "Installing/updating dependencies..."
pip install -q -r requirements.txt

echo ""
echo "Dependencies installed!"
echo ""
echo "Running unit tests..."
pytest tests/ -v

echo ""
echo "Test coverage report:"
pytest tests/ --cov=src --cov-report=term-missing

echo ""
echo "All tests completed!"
