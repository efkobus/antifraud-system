#!/bin/bash

# Script to analyze anti-fraud performance with real CSV data

echo ""
echo "════════════════════════════════════════════════════════════════════"
echo "        Anti-Fraud System - Real Data Analysis"
echo "════════════════════════════════════════════════════════════════════"
echo ""

if [ ! -f "data/transactional-sample.csv" ]; then
    echo "ERROR: data/transactional-sample.csv not found!"
    echo ""
    echo "Please download it from:"
    echo "https://gist.github.com/cloudwalk-tests/76993838e65d7e0f988f40f1b1909c97"
    echo ""
    echo "Or use wget:"
    echo 'wget -O data/transactional-sample.csv "https://gist.githubusercontent.com/cloudwalk-tests/76993838e65d7e0f988f40f1b1909c97/raw/b236c0e375f8f7769c8e5914b6bb88d08b1c563d/transactional-sample.csv"'
    exit 1
fi

if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "ERROR: Virtual environment not found!"
    echo "Run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

export PYTHONPATH="${PYTHONPATH}:$(pwd)"

python3 scripts/analyze_csv_results.py

echo ""
echo "  Database state:"
echo "   - Database updated with CSV data"
echo "   - Chargebacks marked in system"
echo "   - Ready for API testing"
echo ""
echo "  To test the API with this data:"
echo "   uvicorn src.main:app --reload"
echo ""
