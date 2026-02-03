#!/bin/bash
#
# Health Check Script
# Monitors the health of all services
#

# Configuration
API_URL="http://localhost:8000/api/health"
FRONTEND_URL="http://localhost:5001/"
TIMEOUT=10

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "🏥 UPSTOX Platform Health Check"
echo "=========================================="
echo ""

# Function to check service
check_service() {
    local name=$1
    local url=$2
    
    if curl -f -s --max-time $TIMEOUT "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name is healthy"
        return 0
    else
        echo -e "${RED}✗${NC} $name is DOWN"
        return 1
    fi
}

# Function to check systemd service
check_systemd_service() {
    local name=$1
    
    if systemctl is-active --quiet "$name"; then
        echo -e "${GREEN}✓${NC} $name service is running"
        return 0
    else
        echo -e "${RED}✗${NC} $name service is NOT running"
        return 1
    fi
}

# Check systemd services
echo "📋 Checking systemd services..."
check_systemd_service "upstox-api"
check_systemd_service "upstox-frontend"
check_systemd_service "nginx"
echo ""

# Check HTTP endpoints
echo "🌐 Checking HTTP endpoints..."
check_service "API Server" "$API_URL"
check_service "Frontend" "$FRONTEND_URL"
echo ""

# Check database
echo "🗄️  Checking database..."
if [ -f "market_data.db" ]; then
    DB_SIZE=$(du -h market_data.db | cut -f1)
    echo -e "${GREEN}✓${NC} Database exists (Size: $DB_SIZE)"
else
    echo -e "${RED}✗${NC} Database not found"
fi
echo ""

# Check disk space
echo "💾 Checking disk space..."
DISK_USAGE=$(df -h . | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 80 ]; then
    echo -e "${GREEN}✓${NC} Disk usage: ${DISK_USAGE}%"
elif [ "$DISK_USAGE" -lt 90 ]; then
    echo -e "${YELLOW}⚠${NC} Disk usage: ${DISK_USAGE}% (Warning)"
else
    echo -e "${RED}✗${NC} Disk usage: ${DISK_USAGE}% (Critical)"
fi
echo ""

# Check memory
echo "🧠 Checking memory..."
MEM_USAGE=$(free | awk 'NR==2 {printf "%.0f", $3/$2*100}')
if [ "$MEM_USAGE" -lt 80 ]; then
    echo -e "${GREEN}✓${NC} Memory usage: ${MEM_USAGE}%"
elif [ "$MEM_USAGE" -lt 90 ]; then
    echo -e "${YELLOW}⚠${NC} Memory usage: ${MEM_USAGE}% (Warning)"
else
    echo -e "${RED}✗${NC} Memory usage: ${MEM_USAGE}% (Critical)"
fi
echo ""

# Check recent errors in logs
echo "📝 Checking recent errors..."
ERROR_COUNT=$(journalctl -u upstox-api -u upstox-frontend --since "10 minutes ago" | grep -i "error\|critical\|failed" | wc -l)
if [ "$ERROR_COUNT" -eq 0 ]; then
    echo -e "${GREEN}✓${NC} No recent errors in logs"
else
    echo -e "${YELLOW}⚠${NC} Found $ERROR_COUNT error(s) in last 10 minutes"
fi

echo ""
echo "=========================================="
echo "Health check complete"
echo "=========================================="
