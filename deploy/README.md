# QuantumShield — Production Deployment

Scripts for deploying the Flask backend to Oracle Cloud Free Tier ARM VM.

## Quick Start

### 1. Create Oracle Cloud VM
- Sign up at [cloud.oracle.com/free](https://www.oracle.com/cloud/free/)
- Create an **Ampere A1 (ARM)** VM: 2 OCPU / 12 GB RAM
- OS: Ubuntu 22.04 or Oracle Linux 9

### 2. Run Setup Script
```bash
# SSH into your VM
ssh -i ~/key.pem ubuntu@<YOUR_PUBLIC_IP>

# Download and run setup
curl -sSL https://raw.githubusercontent.com/Manimaran-tech/quantumshield/main/deploy/setup_server.sh | bash

# Or with a custom domain:
QS_DOMAIN=api.quantumshield.live bash setup_server.sh
```

### 3. Update Frontend
On your local machine:
```bash
# Edit .env.production → set VITE_API_BASE_URL=https://your-domain-or-ip
npm run build
npx firebase-tools deploy --only hosting
```

## Scripts

| Script | Purpose | Run Where |
|--------|---------|-----------|
| `setup_server.sh` | Full first-time setup | Oracle VM |
| `update.sh` | Pull latest code & restart | Oracle VM |
| `healthcheck.sh` | Verify all services | Oracle VM |

## Useful Commands (on the VM)

```bash
# View live logs
sudo journalctl -u quantumshield -f

# Restart backend
sudo systemctl restart quantumshield

# Check status
sudo systemctl status quantumshield

# Restart Caddy (reverse proxy)
sudo systemctl restart caddy
```

## Cost: ₹0/month (Oracle Always Free Tier)
