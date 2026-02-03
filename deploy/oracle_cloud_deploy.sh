#!/bin/bash
#
# Oracle Cloud Deployment Script
# Automates the deployment process on Oracle Cloud Infrastructure
#

set -e

echo "=========================================="
echo "🚀 Oracle Cloud Deployment"
echo "=========================================="

# Configuration
APP_DIR="/home/opc/upstox-trading-platform"
SERVICE_USER="opc"
VENV_DIR="$APP_DIR/.venv"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    print_error "Please run as root or with sudo"
    exit 1
fi

# Step 1: Install system dependencies
echo ""
echo "Step 1: Installing system dependencies..."
yum update -y
yum install -y python3 python3-pip python3-devel git nginx sqlite
print_status "System dependencies installed"

# Step 2: Create application directory
echo ""
echo "Step 2: Setting up application directory..."
if [ ! -d "$APP_DIR" ]; then
    mkdir -p "$APP_DIR"
    chown $SERVICE_USER:$SERVICE_USER "$APP_DIR"
    print_status "Application directory created"
else
    print_warning "Application directory already exists"
fi

# Step 3: Install Python virtual environment
echo ""
echo "Step 3: Setting up Python virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
    sudo -u $SERVICE_USER python3 -m venv "$VENV_DIR"
    print_status "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# Step 4: Install Python dependencies
echo ""
echo "Step 4: Installing Python dependencies..."
sudo -u $SERVICE_USER $VENV_DIR/bin/pip install --upgrade pip
sudo -u $SERVICE_USER $VENV_DIR/bin/pip install gunicorn
if [ -f "$APP_DIR/requirements.txt" ]; then
    sudo -u $SERVICE_USER $VENV_DIR/bin/pip install -r "$APP_DIR/requirements.txt"
    print_status "Python dependencies installed"
else
    print_warning "requirements.txt not found, skipping"
fi

# Step 5: Create necessary directories
echo ""
echo "Step 5: Creating application directories..."
for dir in logs cache debug_dumps downloads; do
    mkdir -p "$APP_DIR/$dir"
    chown $SERVICE_USER:$SERVICE_USER "$APP_DIR/$dir"
done
print_status "Application directories created"

# Step 6: Copy systemd service files
echo ""
echo "Step 6: Installing systemd services..."
if [ -f "$APP_DIR/deploy/upstox-api.service" ]; then
    cp "$APP_DIR/deploy/upstox-api.service" /etc/systemd/system/
    cp "$APP_DIR/deploy/upstox-frontend.service" /etc/systemd/system/
    systemctl daemon-reload
    print_status "Systemd services installed"
else
    print_warning "Service files not found in $APP_DIR/deploy/"
fi

# Step 7: Configure firewall
echo ""
echo "Step 7: Configuring firewall..."
if command -v firewall-cmd &> /dev/null; then
    firewall-cmd --permanent --add-port=8000/tcp
    firewall-cmd --permanent --add-port=5001/tcp
    firewall-cmd --permanent --add-port=80/tcp
    firewall-cmd --permanent --add-port=443/tcp
    firewall-cmd --reload
    print_status "Firewall configured"
else
    print_warning "firewalld not installed, skipping firewall configuration"
fi

# Step 8: Configure SELinux (if enabled)
echo ""
echo "Step 8: Configuring SELinux..."
if command -v getenforce &> /dev/null && [ "$(getenforce)" != "Disabled" ]; then
    semanage port -a -t http_port_t -p tcp 8000 2>/dev/null || true
    semanage port -a -t http_port_t -p tcp 5001 2>/dev/null || true
    print_status "SELinux configured"
else
    print_warning "SELinux not enabled, skipping"
fi

# Step 9: Setup Nginx reverse proxy
echo ""
echo "Step 9: Configuring Nginx..."
cat > /etc/nginx/conf.d/upstox.conf <<'EOF'
upstream api_backend {
    server 127.0.0.1:8000;
}

upstream frontend_backend {
    server 127.0.0.1:5001;
}

server {
    listen 80;
    server_name _;
    
    # Increase timeouts for long-running requests
    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;
    proxy_read_timeout 300s;
    
    # API endpoints
    location /api/ {
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Frontend
    location / {
        proxy_pass http://frontend_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Static files
    location /static/ {
        alias /home/opc/upstox-trading-platform/static/;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

systemctl enable nginx
systemctl restart nginx
print_status "Nginx configured and started"

# Step 10: Enable and start services
echo ""
echo "Step 10: Starting services..."
systemctl enable upstox-api
systemctl enable upstox-frontend
systemctl start upstox-api
systemctl start upstox-frontend
sleep 5

# Check service status
if systemctl is-active --quiet upstox-api; then
    print_status "API service is running"
else
    print_error "API service failed to start"
fi

if systemctl is-active --quiet upstox-frontend; then
    print_status "Frontend service is running"
else
    print_error "Frontend service failed to start"
fi

# Step 11: Display summary
echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "📡 Services:"
echo "   API Server:      systemctl status upstox-api"
echo "   Frontend:        systemctl status upstox-frontend"
echo ""
echo "🌐 Access:"
echo "   Frontend:        http://$(hostname -I | awk '{print $1}')"
echo "   API:             http://$(hostname -I | awk '{print $1}')/api/health"
echo ""
echo "📝 Logs:"
echo "   API:             journalctl -u upstox-api -f"
echo "   Frontend:        journalctl -u upstox-frontend -f"
echo "   Nginx:           tail -f /var/log/nginx/error.log"
echo ""
echo "🔧 Management:"
echo "   Restart API:     systemctl restart upstox-api"
echo "   Restart Frontend: systemctl restart upstox-frontend"
echo "   Stop All:        systemctl stop upstox-api upstox-frontend"
echo ""
echo "⚠️  Next Steps:"
echo "   1. Configure .env file with your Upstox credentials"
echo "   2. Set up SSL certificate for HTTPS"
echo "   3. Configure backup schedule for database"
echo "   4. Set up monitoring and alerting"
echo "=========================================="
