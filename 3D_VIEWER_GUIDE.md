# 3D Projection Viewer - User Guide

## Quick Start

```bash
# Launch viewer for any projection
./launch_viewer_3d.sh projections/projection_1_t0.2_d1.json

# Or specify custom port
./launch_viewer_3d.sh projections/projection_5_t0.7_d2.json 8080

# Or use Python directly
python src/visualization/server_3d.py projections/projection_1_t0.2_d1.json 8000
```

Then open your browser to: **http://127.0.0.1:8000**

## What You'll See

### 3D Graph Visualization

- **Blue spheres** = Atomic nodes (knowledge statements)
- **Gray spheres** = Context nodes (source documents)
- **Cyan lines** = Related-to relationships
- **Red lines** = Depends-on relationships
- **White lines** = Appears-in relationships

### Size & Glow

- **Larger nodes** = Higher degree (more connections)
- **Glowing nodes** = Hub nodes in the network

### Interactive Controls

| Action | Control |
|--------|---------|
| **Rotate view** | Arrow keys |
| **Pan camera** | Click & drag mouse |
| **Zoom** | Scroll wheel |
| **Select node** | Click on sphere |
| **View details** | Details panel appears on right |

## Understanding the Visualization

### Info Panel (Top Left)

Shows projection parameters:
- **Focus Node**: Starting point of projection
- **Threshold**: Coherence threshold used
- **Max Depth**: Graph traversal depth
- **Nodes/Edges**: Graph size metrics
- **Max Degree**: Highest connectivity node

### Details Panel (Top Right)

When you click a node:
- Full statement text
- Canonical terms
- Evidence count
- 3D position coordinates
- Network degree

### 3D Layout Algorithm

The visualization uses **deterministic force-directed layout**:

1. **Repulsion**: Nodes push each other apart (like magnets)
2. **Attraction**: Connected nodes pull together (like springs)
3. **Weight**: Stronger relationships = stronger attraction
4. **Convergence**: 200 iterations for stable layout

**Key Property**: Same projection parameters always produce the same layout.

## Comparing Projections

Open multiple projections side-by-side to see how parameters affect topology:

### Threshold Comparison

```bash
# Dense graph (low threshold)
python src/visualization/server_3d.py projections/projection_1_t0.2_d1.json 8000

# Sparse graph (high threshold) - open in different terminal/port
python src/visualization/server_3d.py projections/projection_7_t0.9_d1.json 8001
```

**What to observe:**
- Low threshold → Many connections, tight clusters
- High threshold → Few connections, isolated nodes

### Depth Comparison

```bash
# Shallow projection (depth=1)
python src/visualization/server_3d.py projections/projection_1_t0.2_d1.json 8000

# Deep projection (depth=5)
python src/visualization/server_3d.py projections/projection_2_t0.2_d5.json 8001
```

**What to observe:**
- Shallow → Immediate neighbors only
- Deep → Cascading structure, more nodes

### Hub Suppression (top_k)

```bash
# No hub suppression
python src/visualization/server_3d.py projections/projection_1_t0.2_d1.json 8000

# With top_k=3 (hub suppression)
python src/visualization/server_3d.py projections/projection_1_t0.2_k5_d1.json 8001
```

**What to observe:**
- Without top_k → Dense hubs visible
- With top_k → More distributed connectivity

## Exporting Snapshots

You can pre-generate 3D snapshots without starting the server:

```bash
# Create standalone snapshot JSON
python src/visualization/snapshot_adapter_3d.py \
    projections/projection_1_t0.2_d1.json \
    snapshots/my_snapshot_3d.json
```

This is useful for:
- Batch processing multiple projections
- Archiving specific layouts
- Custom frontend development

## Tips for Exploration

### Finding Hub Nodes
1. Look for **large, glowing spheres**
2. Click to see degree in details panel
3. High degree = semantic hub

### Identifying Clusters
1. Rotate to see structure from different angles
2. Isolated groups = distinct semantic clusters
3. Dense connections = strongly related concepts

### Tracing Relationships
1. Click a node to highlight it
2. Follow colored edges to connected nodes
3. Edge opacity = relationship strength

### Performance
- **Smooth rendering**: Modern GPU required
- **Label limits**: Max 30 labels shown at once (LOD)
- **Browser**: Chrome/Firefox recommended

## Keyboard Shortcuts Reference

```
↑ ↓ ← →     Rotate camera view
Mouse Drag   Pan camera position
Scroll       Zoom in/out
Click        Select node and show details
```

## API Access

The server provides REST API endpoints:

### Get Snapshot Data
```bash
curl http://127.0.0.1:8000/api/snapshot
```

### Get Node Details
```bash
curl http://127.0.0.1:8000/api/node/atomic_28cf70b6fc7a9bce
```

### Health Check
```bash
curl http://127.0.0.1:8000/api/health
```

## Troubleshooting

### Black Screen
- **Cause**: WebGL not supported or Three.js failed to load
- **Fix**: Use a modern browser (Chrome, Firefox, Edge)
- **Check**: Browser console (F12) for errors

### No Labels Appearing
- **Cause**: Too far from nodes or LOD limit
- **Fix**: Zoom closer to a cluster of nodes
- **Note**: Maximum 30 labels displayed at once

### Server Won't Start
- **Cause**: Flask not installed
- **Fix**: `pip install flask>=2.3.0`
- **Check**: Port 8000 not already in use

### Different Layout Each Time
- **Cause**: Projection file changed
- **Fix**: Verify projection parameters are identical
- **Note**: Same input = same layout (deterministic)

### Slow Performance
- **Cause**: Too many nodes or edges
- **Fix**: Use higher threshold or lower depth
- **Optimize**: Close other browser tabs

## Advanced Usage

### Custom Port
```bash
python src/visualization/server_3d.py projections/my_proj.json 9000
```

### Embedding in Jupyter
```python
from IPython.display import IFrame
IFrame('http://127.0.0.1:8000', width=1200, height=800)
```

### Batch Snapshot Generation
```bash
# Generate all snapshots
for proj in projections/*.json; do
    output="snapshots/$(basename $proj .json)_3d.json"
    python src/visualization/snapshot_adapter_3d.py "$proj" "$output"
done
```

## Visual Encoding Summary

| **Visual Property** | **Meaning** | **Range** |
|---------------------|-------------|-----------|
| Sphere size | Node degree | 0.5 - 2.5 units |
| Sphere color | Node type | Blue/Gray |
| Emissive glow | Hub strength | 0 - 0.5 intensity |
| Edge opacity | Relationship weight | 0.2 - 1.0 |
| Edge color | Relationship type | Cyan/Red/White |
| Position (x,y,z) | Semantic similarity | Force-directed |

## Next Steps

- **Analyze**: Click nodes to understand the knowledge graph
- **Compare**: Open multiple projections to see parameter effects
- **Export**: Generate snapshots for documentation
- **Integrate**: Use API endpoints in custom applications

## Questions?

See [viewer/README.md](viewer/README.md) for technical details and architecture.
