#!/bin/bash
###############################################################################
# QuantumShield — Oracle Cloud ARM VM Setup Script
# 
# Usage: SSH into your Oracle Cloud VM and run:
#   curl -sSL https://raw.githubusercontent.com/Manimaran-tech/quantumshield/main/deploy/setup_server.sh | bash
#   -- OR --
#   scp deploy/setup_server.sh ubuntu@<YOUR_IP>:~ && ssh ubuntu@<YOUR_IP> 'bash setup_server.sh'
#
# What this does:
#   1. Installs Python 3.10, build tools, git
#   2. Clones the QuantumShield repo
#   3. Creates venv and installs all Python dependencies
#   4. Installs Caddy (reverse proxy with auto-HTTPS)
#   5. Creates systemd service (auto-start on boot)
#   6. Opens firewall ports (80, 443, 5000)
#   7. Starts everything
###############################################################################

set -euo pipefail

# ─── Configuration ──────────────────────────────────────────────────────────
REPO_URL="https://github.com/Manimaran-tech/quantumshield.git"
APP_DIR="$HOME/quantumshield"
VENV_DIR="$APP_DIR/venv"
SERVICE_NAME="quantumshield"
FLASK_PORT=5000
# Set your domain here (or leave empty to use IP-only mode)
DOMAIN="${QS_DOMAIN:-}"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║   QuantumShield — Oracle Cloud Production Deployment    ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  ARM VM • Flask + Gunicorn • Caddy HTTPS • systemd      ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# ─── Detect OS ──────────────────────────────────────────────────────────────
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS_ID="$ID"
    echo "✓ Detected OS: $PRETTY_NAME"
else
    echo "⚠ Could not detect OS. Assuming Ubuntu/Debian."
    OS_ID="ubuntu"
fi

# ─── Step 1: System packages ───────────────────────────────────────────────
echo ""
echo "━━━ Step 1/7: Installing system packages ━━━"

if [[ "$OS_ID" == "ubuntu" || "$OS_ID" == "debian" ]]; then
    sudo apt update -y
    sudo apt install -y python3 python3-venv python3-pip python3-dev \
        build-essential libffi-dev libssl-dev libxrender1 libxext6 \
        git curl wget unzip
elif [[ "$OS_ID" == "ol" || "$OS_ID" == "centos" || "$OS_ID" == "rhel" || "$OS_ID" == "almalinux" ]]; then
    sudo dnf install -y python3 python3-pip python3-devel \
        gcc gcc-c++ make libffi-devel openssl-devel \
        git curl wget unzip
else
    echo "⚠ Unknown OS '$OS_ID'. Trying apt..."
    sudo apt update -y && sudo apt install -y python3 python3-venv python3-pip git curl
fi

PYTHON_CMD=$(command -v python3.10 || command -v python3.11 || command -v python3.12 || command -v python3)
echo "✓ Using Python: $($PYTHON_CMD --version)"

# ─── Step 2: Clone repo ────────────────────────────────────────────────────
echo ""
echo "━━━ Step 2/7: Cloning QuantumShield repository ━━━"

if [ -d "$APP_DIR" ]; then
    echo "  Directory exists. Pulling latest..."
    cd "$APP_DIR"
    git pull origin main || git pull origin master || echo "⚠ Git pull failed, continuing with existing code"
else
    git clone "$REPO_URL" "$APP_DIR"
    cd "$APP_DIR"
fi
echo "✓ Repository ready at $APP_DIR"

# ─── Step 3: Python virtual environment + dependencies ─────────────────────
echo ""
echo "━━━ Step 3/7: Setting up Python environment ━━━"

if [ ! -d "$VENV_DIR" ]; then
    $PYTHON_CMD -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"

pip install --upgrade pip setuptools wheel
echo "  Installing requirements.txt (this may take 5-10 minutes on first run)..."
pip install -r requirements.txt

# Install Gunicorn for production serving
pip install gunicorn

echo "✓ Python environment ready ($($PYTHON_CMD --version), $(pip --version | cut -d' ' -f1-2))"

# ─── Step 4: Create .env file ──────────────────────────────────────────────
echo ""
echo "━━━ Step 4/7: Setting up environment variables ━━━"

if [ ! -f "$APP_DIR/.env" ]; then
    cat > "$APP_DIR/.env" << 'ENVEOF'
# QuantumShield Backend Environment
# Add your API keys here:
GEMINI_API_KEY=your-gemini-api-key
# MYUPCHAR_API_KEY=your-myupchar-key
ENVEOF
    echo "⚠ Created .env with placeholder keys. Edit with: nano $APP_DIR/.env"
else
    echo "✓ .env file already exists"
fi

# ─── Step 5: Install Caddy reverse proxy ───────────────────────────────────
echo ""
echo "━━━ Step 5/7: Installing Caddy (reverse proxy + auto-HTTPS) ━━━"

if ! command -v caddy &> /dev/null; then
    if [[ "$OS_ID" == "ubuntu" || "$OS_ID" == "debian" ]]; then
        sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
        curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg 2>/dev/null
        curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list > /dev/null
        sudo apt update -y
        sudo apt install -y caddy
    elif [[ "$OS_ID" == "ol" || "$OS_ID" == "centos" || "$OS_ID" == "rhel" || "$OS_ID" == "almalinux" ]]; then
        sudo dnf install -y 'dnf-command(copr)'
        sudo dnf copr enable -y @caddy/caddy
        sudo dnf install -y caddy
    fi
    echo "✓ Caddy installed"
else
    echo "✓ Caddy already installed ($(caddy version))"
fi

# Configure Caddy
if [ -n "$DOMAIN" ]; then
    echo "  Configuring Caddy for domain: $DOMAIN"
    sudo tee /etc/caddy/Caddyfile > /dev/null << CADDYEOF
$DOMAIN {
    reverse_proxy localhost:$FLASK_PORT

    header {
        Access-Control-Allow-Origin  *
        Access-Control-Allow-Methods "GET, POST, OPTIONS"
        Access-Control-Allow-Headers "Content-Type, Authorization"
    }

    # Increase timeout for heavy ML endpoints (QRL, VQE, generation)
    reverse_proxy localhost:$FLASK_PORT {
        transport http {
            response_header_timeout 120s
            dial_timeout 30s
        }
    }
}
CADDYEOF
else
    echo "  No domain set. Configuring Caddy for direct IP access on :80"
    sudo tee /etc/caddy/Caddyfile > /dev/null << CADDYEOF
:80 {
    reverse_proxy localhost:$FLASK_PORT

    header {
        Access-Control-Allow-Origin  *
        Access-Control-Allow-Methods "GET, POST, OPTIONS"
        Access-Control-Allow-Headers "Content-Type, Authorization"
    }
}
CADDYEOF
fi

sudo systemctl restart caddy
sudo systemctl enable caddy
echo "✓ Caddy configured and running"

# ─── Step 6: Open firewall ports ───────────────────────────────────────────
echo ""
echo "━━━ Step 6/7: Opening firewall ports (80, 443, 5000) ━━━"

if command -v firewall-cmd &> /dev/null; then
    # Oracle Linux / RHEL
    sudo firewall-cmd --permanent --add-port=80/tcp 2>/dev/null || true
    sudo firewall-cmd --permanent --add-port=443/tcp 2>/dev/null || true
    sudo firewall-cmd --permanent --add-port=5000/tcp 2>/dev/null || true
    sudo firewall-cmd --reload 2>/dev/null || true
    echo "✓ firewalld rules added"
elif command -v ufw &> /dev/null; then
    # Ubuntu
    sudo ufw allow 80/tcp 2>/dev/null || true
    sudo ufw allow 443/tcp 2>/dev/null || true
    sudo ufw allow 5000/tcp 2>/dev/null || true
    echo "✓ ufw rules added"
else
    # Raw iptables
    sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT 2>/dev/null || true
    sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT 2>/dev/null || true
    sudo iptables -I INPUT -p tcp --dport 5000 -j ACCEPT 2>/dev/null || true
    if command -v netfilter-persistent &> /dev/null; then
        sudo netfilter-persistent save 2>/dev/null || true
    fi
    echo "✓ iptables rules added"
fi

echo ""
echo "⚠ IMPORTANT: Also open ports 80, 443, 5000 in the Oracle Cloud Console:"
echo "  Networking → VCN → Subnets → Security Lists → Add Ingress Rules"

# ─── Step 7: Create systemd service ────────────────────────────────────────
echo ""
echo "━━━ Step 7/7: Creating systemd service ━━━"

CURRENT_USER=$(whoami)

sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null << SVCEOF
[Unit]
Description=QuantumShield Flask Backend (Gunicorn)
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=$CURRENT_USER
Group=$CURRENT_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$VENV_DIR/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONUNBUFFERED=1"
EnvironmentFile=$APP_DIR/.env

# Gunicorn: 2 workers, 120s timeout for heavy ML endpoints
ExecStart=$VENV_DIR/bin/gunicorn \
    --workers 2 \
    --threads 4 \
    --bind 0.0.0.0:$FLASK_PORT \
    --timeout 120 \
    --graceful-timeout 30 \
    --access-logfile - \
    --error-logfile - \
    app:app

Restart=always
RestartSec=5
StartLimitBurst=5
StartLimitIntervalSec=60

# Memory watchdog — restart if backend exceeds 10 GB
MemoryMax=10G

[Install]
WantedBy=multi-user.target
SVCEOF

sudo systemctl daemon-reload
sudo systemctl start "$SERVICE_NAME"
sudo systemctl enable "$SERVICE_NAME"

echo "✓ systemd service created and started"

# ─── Done! ──────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║              ✅ DEPLOYMENT COMPLETE!                     ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║                                                          ║"
echo "║  Backend running on: http://$(hostname -I | awk '{print $1}'):$FLASK_PORT    "
if [ -n "$DOMAIN" ]; then
echo "║  HTTPS endpoint:     https://$DOMAIN                     "
fi
echo "║                                                          ║"
echo "║  Useful commands:                                        ║"
echo "║    Status:   sudo systemctl status $SERVICE_NAME         ║"
echo "║    Logs:     sudo journalctl -u $SERVICE_NAME -f         ║"
echo "║    Restart:  sudo systemctl restart $SERVICE_NAME        ║"
echo "║    Stop:     sudo systemctl stop $SERVICE_NAME           ║"
echo "║                                                          ║"
echo "║  Test:                                                   ║"
echo "║    curl http://localhost:$FLASK_PORT/api/disease/modalities"
echo "║                                                          ║"
echo "║  Next: Update .env.production on your local machine      ║"
echo "║  and run: npm run build && firebase deploy               ║"
echo "╚══════════════════════════════════════════════════════════╝"
