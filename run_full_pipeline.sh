#!/bin/bash
# Full pipeline: Ingestion → Projection → Visualization
# For ChatGPT conversations export

set -e

GRAPH_FILE="chatgpt_graph.json"
PROJECTION_FILE="projections/chatgpt_projection.json"
SNAPSHOT_FILE="snapshots/chatgpt_snapshot.json"
PORT=8000

echo "========================================="
echo "CHATGPT KNOWLEDGE GRAPH PIPELINE"
echo "========================================="
echo

# Wait for ingestion to complete
echo "[1/4] Waiting for ingestion to complete..."
while ! [ -f "$GRAPH_FILE" ]; do
    sleep 5
    if ps -p 3304622 > /dev/null 2>&1; then
        tail -3 ingestion.log | grep -E "Processing chunk|messages" | tail -1 || echo -n "."
    else
        echo
        echo "✗ Ingestion process finished but no output file found"
        echo "Check ingestion.log for errors"
        exit 1
    fi
done

echo
echo "✓ Graph file created: $GRAPH_FILE"
echo

# Show statistics
echo "[2/4] Graph Statistics:"
python main.py stats "$GRAPH_FILE" | head -30
echo

# Find a good focus node (one with high connectivity)
echo "[3/4] Finding focus node and creating projection..."
FOCUS_NODE=$(python3 << 'EOF'
import json
with open('chatgpt_graph.json', 'r') as f:
    graph = json.load(f)

# Find atomic nodes sorted by number of edges
nodes = graph['nodes_added']
atomic_nodes = [n for n in nodes if n['node_type'] == 'atomic']

if not atomic_nodes:
    print("ERROR: No atomic nodes found")
    exit(1)

# Count edges per node
edge_counts = {}
for edge in graph.get('edges_added', []) + graph.get('weights_added', []):
    src, tgt = edge.get('source'), edge.get('target')
    edge_counts[src] = edge_counts.get(src, 0) + 1
    edge_counts[tgt] = edge_counts.get(tgt, 0) + 1

# Find node with most edges
best_node = max(atomic_nodes, key=lambda n: edge_counts.get(n['node_id'], 0))
print(best_node['node_id'])
EOF
)

if [ -z "$FOCUS_NODE" ]; then
    echo "✗ Failed to find focus node"
    exit 1
fi

echo "  Focus node: $FOCUS_NODE"
echo "  Creating projection..."

# Create projection
python main.py project "$GRAPH_FILE" "$FOCUS_NODE" -o projections/

# Find the most recent projection file
LATEST_PROJECTION=$(ls -t projections/projection_*.json 2>/dev/null | head -1)

if [ -z "$LATEST_PROJECTION" ]; then
    echo "✗ No projection files created"
    exit 1
fi

echo "✓ Projection created: $LATEST_PROJECTION"
echo

# Create 3D snapshot
echo "[4/4] Creating 3D visualization snapshot..."
python src/visualization/snapshot_adapter_3d.py "$LATEST_PROJECTION" "$SNAPSHOT_FILE"
echo "✓ Snapshot created: $SNAPSHOT_FILE"
echo

# Kill any existing server
pkill -9 -f "server_3d.py" 2>/dev/null || true
sleep 2

# Start visualization server
echo "========================================="
echo "Starting 3D visualization server..."
echo "========================================="
echo
echo "Server will start on: http://127.0.0.1:$PORT"
echo
echo "Open your browser to view the interactive 3D knowledge graph!"
echo

python src/visualization/server_3d.py "$LATEST_PROJECTION" "$PORT"
