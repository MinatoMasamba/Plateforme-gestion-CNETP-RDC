#!/bin/bash

###############################################################################
# CNETP Django-React Hybrid - Development Setup & Run Script
###############################################################################

set -e

PROJECT_DIR="/home/minato/projet"
FRONTEND_DIR="$PROJECT_DIR/frontend"
DJANGO_DIR="$PROJECT_DIR"

echo "═══════════════════════════════════════════════════════════════"
echo "🚀 CNETP Django-React Hybrid - Development Environment"
echo "═══════════════════════════════════════════════════════════════"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if frontend dependencies are installed
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo -e "${YELLOW}📦 Installing frontend dependencies...${NC}"
    cd "$FRONTEND_DIR"
    npm install
    echo -e "${GREEN}✅ Frontend dependencies installed${NC}"
fi

echo ""
echo -e "${BLUE}Starting development servers...${NC}"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down servers...${NC}"
    kill $FRONTEND_PID $DJANGO_PID 2>/dev/null || true
    echo -e "${GREEN}Done!${NC}"
}

trap cleanup EXIT

# Start Vite dev server
echo -e "${BLUE}🎨 Starting React (Vite) on http://localhost:5173${NC}"
cd "$FRONTEND_DIR"
npm run dev &
FRONTEND_PID=$!

# Start Django dev server
echo -e "${BLUE}🔷 Starting Django on http://localhost:8000${NC}"
cd "$DJANGO_DIR"
source mon_env/bin/activate

# Run migrations if needed
python manage.py migrate --noinput

# Start server
python manage.py runserver 0.0.0.0:8000 &
DJANGO_PID=$!

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ Development environment is ready!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📍 Frontend (Vite):  http://localhost:5173"
echo "📍 Django Server:    http://localhost:8000"
echo "📍 Django Admin:     http://localhost:8000/admin"
echo "📍 API Docs:         http://localhost:8000/api/v1/schema/swagger/"
echo ""
echo "🔐 CSRF Token: Auto-handled in requests"
echo "🍪 Session: Django sessionid cookie"
echo ""
echo "Press Ctrl+C to stop all servers"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Keep script running
wait
