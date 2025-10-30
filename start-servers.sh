#!/bin/bash

# ============================================================================
# Orion Monitoring Dashboard - Server Startup Script
# ============================================================================

echo "🚀 Starting Orion Monitoring Services..."
echo "========================================"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Change to dashboard directory
cd /var/www/html/new-config-manager/monitoring-dashboard

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Stop existing processes
echo "Stopping existing servers..."
pkill -f "auth-server.js" 2>/dev/null
pkill -f "npm run dev" 2>/dev/null
sudo pkill -f "next-server" 2>/dev/null
sleep 3

# Clear Next.js cache if exists
if [ -d ".next" ]; then
    echo "Clearing Next.js cache..."
    rm -rf .next
fi

# Start Authentication Server
echo ""
echo "Starting Authentication Server..."
node backend/auth-server.js > /tmp/auth-server.log 2>&1 &
AUTH_PID=$!
sleep 3

if check_port 5001; then
    echo -e "${GREEN}✅ Authentication Server started (Port 5001)${NC}"
else
    echo -e "${RED}❌ Failed to start Authentication Server${NC}"
    exit 1
fi

# Start Dashboard
echo ""
echo "Starting Dashboard..."
npm run dev > /tmp/dashboard.log 2>&1 &
DASH_PID=$!
sleep 8

if check_port 3001 || check_port 3000; then
    echo -e "${GREEN}✅ Dashboard started (Check port 3000-3001)${NC}"
else
    echo -e "${RED}❌ Failed to start Dashboard${NC}"
    exit 1
fi

# Display status
echo ""
echo "========================================"
echo -e "${GREEN}🎉 All Services Started Successfully!${NC}"
echo "========================================"
echo ""
echo "📊 Dashboard:      http://192.168.1.15:3001"
echo "🔐 Auth Server:    http://192.168.1.15:5001"
echo ""
echo "📝 Logs:"
echo "   Dashboard:      tail -f /tmp/dashboard.log"
echo "   Auth Server:    tail -f /tmp/auth-server.log"
echo ""
echo "🔄 To restart servers, run this script again:"
echo "   ./start-servers.sh"
echo ""


