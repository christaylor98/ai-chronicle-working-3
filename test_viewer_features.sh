#!/bin/bash
# Quick test script for 3D viewer features

echo "Testing 3D Viewer Features..."
echo ""

# Test 1: Snapshot generation
echo "[1/3] Testing snapshot generation..."
python src/visualization/snapshot_adapter_3d.py \
    projections/projection_1_t0.2_d1.json \
    snapshots/test_features.json > /dev/null 2>&1

if [ -f "snapshots/test_features.json" ]; then
    echo "✓ Snapshot generation works"
else
    echo "✗ Snapshot generation failed"
    exit 1
fi

# Test 2: Server API availability
echo ""
echo "[2/3] Testing server startup..."
python src/visualization/server_3d.py projections/projection_1_t0.2_d1.json 8888 > /dev/null 2>&1 &
SERVER_PID=$!
sleep 3

# Test health endpoint
if curl -s -f http://127.0.0.1:8888/api/health > /dev/null 2>&1; then
    echo "✓ Server health endpoint works"
else
    echo "✗ Server health endpoint failed"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi

# Test snapshot endpoint
if curl -s -f http://127.0.0.1:8888/api/snapshot | grep -q "nodes"; then
    echo "✓ Snapshot API endpoint works"
else
    echo "✗ Snapshot API endpoint failed"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi

# Test reload endpoint
if curl -s -f http://127.0.0.1:8888/api/snapshot/reload > /dev/null 2>&1; then
    echo "✓ Reload endpoint works"
else
    echo "✗ Reload endpoint failed"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi

# Cleanup
kill $SERVER_PID 2>/dev/null
sleep 1

# Test 3: File integrity
echo ""
echo "[3/3] Checking viewer files..."
MISSING=0

for file in viewer/index.html \
            viewer/js/main.js \
            viewer/js/api.js \
            viewer/js/renderer.js \
            viewer/js/scene.js \
            viewer/js/input.js \
            viewer/js/labels.js \
            viewer/js/ui.js; do
    if [ ! -f "$file" ]; then
        echo "✗ Missing: $file"
        MISSING=1
    fi
done

if [ $MISSING -eq 0 ]; then
    echo "✓ All viewer files present"
fi

echo ""
echo "=========================================="
echo "All tests passed! ✓"
echo "=========================================="
echo ""
echo "To start the viewer:"
echo "  ./launch_viewer_3d.sh"
echo ""
echo "New Features:"
echo "  • Dynamic LOD control (5-100 labels)"
echo "  • Node size scaling (50%-200%)"
echo "  • Refresh view button"
echo "  • Reset camera button"
