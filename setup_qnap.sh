#!/bin/bash

echo "============================================"
echo "Stock Analysis Tool - QNAP TS464 Setup"
echo "============================================"
echo

# Check if running on QNAP
if [ ! -f "/etc/config/qpkg.conf" ]; then
    echo "WARNING: This script is designed for QNAP NAS"
    echo "Continue anyway? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "[1] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found"
    echo "Please install Python 3.8+ via App Center"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | cut -d" " -f2 | cut -d"." -f1,2)
echo "Found Python $PYTHON_VERSION"

echo "[2] Creating data directories..."
mkdir -p data/database/backups
mkdir -p data/cache
mkdir -p data/exports
mkdir -p logs
chmod -R 755 data logs

echo "[3] Setting up Python environment..."
python3 -m pip install --user --upgrade pip
python3 -m pip install --user -r requirements.txt

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install Python dependencies"
    echo "Check internet connection and requirements.txt"
    exit 1
fi

echo "[4] Setting up environment configuration..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "Created .env file from .env.example"
    else
        cat > .env << 'EOF'
# Stock Analysis Tool - Production Configuration
SECRET_KEY=qnap-stock-analysis-production-key-2025
FLASK_ENV=production
FLASK_DEBUG=False
PORT=5000
DATABASE_PATH=data/database/analysis.db
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
CACHE_TIMEOUT=3600
ENABLE_CACHE=True
EOF
        echo "Created basic .env file"
    fi
fi

echo "[5] Setting file permissions..."
chmod +x cgi_app.py
chmod 644 .env
chmod -R 644 templates/* analyzers/* routes/* utils/*
chmod +x *.sh

echo "[6] Testing Python imports..."
python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from app import app
    print('✓ Flask app import successful')
except Exception as e:
    print(f'✗ Import error: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "ERROR: Python import test failed"
    exit 1
fi

echo
echo "============================================"
echo "QNAP Setup Complete!"
echo "============================================"
echo
echo "Next Steps:"
echo "1. Configure WebStation Virtual Host"
echo "2. Set Document Root: $(pwd)"
echo "3. Enable Python CGI support"
echo "4. Access via: http://your-nas-ip/stock-analysis"
echo
echo "For detailed WebStation configuration:"
echo "See QNAP_DEPLOY.md"
echo