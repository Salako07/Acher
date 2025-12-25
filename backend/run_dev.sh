#!/bin/bash

echo "Starting Accountability System Backend..."
echo ""

# Activate virtual environment
if [ -f venv/bin/activate ]; then
    source venv/bin/activate
else
    echo "ERROR: Virtual environment not found!"
    echo "Please run: python3 -m venv venv"
    exit 1
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "WARNING: .env file not found!"
    echo "Creating from .env.example..."
    cp .env.example .env
    echo ""
    echo "IMPORTANT: Edit .env file with your database credentials and SECRET_KEY"
    echo "Then run this script again."
    exit 1
fi

# Start the server
echo "Starting FastAPI server on http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo ""
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
