#!/bin/bash
###############################################################################
# QuantumShield — Quick Health Check & Diagnostics
#
# Run on the Oracle VM to verify everything is working:
#   bash deploy/healthcheck.sh
###############################################################################

set -euo pipefail

echo "═══ QuantumShield Health Check ═══"
echo ""

# 1. Service status
echo "1. Service Status:"
if systemctl is-active --quiet quantumshield; then
    echo "   ✅ quantumshield service is RUNNING"
else
    echo "   ❌ quantumshield service is NOT running"
    echo "   → Run: sudo systemctl start quantumshield"
    echo "   → Logs: sudo journalctl -u quantumshield -n 50"
fi

# 2. Caddy status
echo ""
echo "2. Caddy (Reverse Proxy) Status:"
if systemctl is-active --quiet caddy; then
    echo "   ✅ Caddy is RUNNING"
else
    echo "   ❌ Caddy is NOT running"
    echo "   → Run: sudo systemctl start caddy"
fi

# 3. Port check
echo ""
echo "3. Port Check:"
if ss -tlnp | grep -q ":5000"; then
    echo "   ✅ Port 5000 is LISTENING"
else
    echo "   ❌ Port 5000 is NOT listening"
fi

if ss -tlnp | grep -q ":80"; then
    echo "   ✅ Port 80 is LISTENING (Caddy)"
else
    echo "   ⚠  Port 80 is not listening"
fi

if ss -tlnp | grep -q ":443"; then
    echo "   ✅ Port 443 is LISTENING (Caddy HTTPS)"
else
    echo "   ⚠  Port 443 is not listening (need domain for HTTPS)"
fi

# 4. API endpoint test
echo ""
echo "4. API Endpoint Tests:"

test_endpoint() {
    local name="$1"
    local url="$2"
    local method="${3:-GET}"
    local data="${4:-}"
    
    if [ "$method" == "POST" ]; then
        response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$url" \
            -H "Content-Type: application/json" -d "$data" --max-time 10 2>/dev/null) || response="FAIL"
    else
        response=$(curl -s -o /dev/null -w "%{http_code}" "$url" --max-time 10 2>/dev/null) || response="FAIL"
    fi
    
    if [ "$response" == "200" ]; then
        echo "   ✅ $name → HTTP $response"
    else
        echo "   ❌ $name → HTTP $response"
    fi
}

test_endpoint "Modalities" "http://localhost:5000/api/disease/modalities"
test_endpoint "Pathogen Lookup" "http://localhost:5000/api/pathogen/lookup" "POST" '{"pathogen_name":"Tuberculosis"}'
test_endpoint "History" "http://localhost:5000/history"

# 5. System resources
echo ""
echo "5. System Resources:"
echo "   CPU:    $(nproc) cores"
echo "   RAM:    $(free -h | awk '/^Mem:/{print $3 "/" $2}') used"
echo "   Disk:   $(df -h / | awk 'NR==2{print $3 "/" $2 " (" $5 " used)"}')"

# 6. Public IP
echo ""
echo "6. Public IP:"
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "Could not determine")
echo "   $PUBLIC_IP"
echo "   Test from outside: curl http://$PUBLIC_IP:5000/api/disease/modalities"

echo ""
echo "═══ Health Check Complete ═══"
