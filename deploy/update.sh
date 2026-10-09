#!/bin/bash
###############################################################################
# QuantumShield — Update & Redeploy (run on Oracle VM)
#
# Pulls latest code from GitHub and restarts the backend.
# Usage: bash deploy/update.sh
###############################################################################

set -euo pipefail

APP_DIR="$HOME/quantumshield"

echo "═══ QuantumShield Update ═══"

cd "$APP_DIR"

echo "1. Pulling latest code..."
git pull origin main || git pull origin master

echo "2. Activating virtual environment..."
source venv/bin/activate

echo "3. Installing any new dependencies..."
pip install -r requirements.txt --quiet

echo "4. Restarting backend service..."
sudo systemctl restart quantumshield

echo "5. Waiting 3 seconds for startup..."
sleep 3

echo "6. Verifying..."
if systemctl is-active --quiet quantumshield; then
    echo "   ✅ Backend restarted successfully"
    curl -s http://localhost:5000/api/disease/modalities | head -c 100
    echo ""
else
    echo "   ❌ Backend failed to start"
    sudo journalctl -u quantumshield -n 20 --no-pager
fi

echo ""
echo "═══ Update Complete ═══"
