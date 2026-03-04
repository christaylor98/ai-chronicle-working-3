#!/bin/bash

# 3D Viewer Quick Launch Script
# Usage: ./launch_viewer_3d.sh [projection_file] [port]

set -e

# Default values
PROJECTION="${1:-projections/projection_1_t0.2_d1.json}"
PORT="${2:-8000}"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  3D Projection Viewer - Launch Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if projection file exists
if [ ! -f "$PROJECTION" ]; then
    echo -e "${YELLOW}Error: Projection file not found: $PROJECTION${NC}"
    echo ""
    echo "Available projections:"
    ls -1 projections/*.json | head -5
    exit 1
fi

# Check Flask installation
echo -e "${BLUE}[1/3]${NC} Checking dependencies..."
if ! python -c "import flask" 2>/dev/null; then
    echo -e "${YELLOW}Flask not found. Installing...${NC}"
    pip install flask>=2.3.0
fi
echo -e "${GREEN}✓ Flask installed${NC}"

# Display projection info
echo ""
echo -e "${BLUE}[2/3]${NC} Loading projection..."
echo "  File: $PROJECTION"
echo "  Port: $PORT"
echo ""

# Start server
echo -e "${BLUE}[3/3]${NC} Starting server..."
echo ""
echo -e "${GREEN}✓ Server starting on http://127.0.0.1:${PORT}${NC}"
echo ""
echo -e "Press ${YELLOW}Ctrl+C${NC} to stop the server"
echo ""

# Run server
python src/visualization/server_3d.py "$PROJECTION" "$PORT"
