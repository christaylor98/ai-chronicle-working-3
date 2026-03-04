# 3D Projection Viewer

Interactive 3D visualization system for AI Chronicle projection graphs using Three.js.

## Overview

The 3D Projection Viewer implements the **PROJECTION_TO_3D_SNAPSHOT_ADAPTER.v1.0** specification, providing deterministic 3D visualization of relational knowledge fabric projections.

### Architecture

```
┌─────────────────────┐
│ Projection JSON     │ (input)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ snapshot_adapter_3d │ (Python)
│ - 3D Force Layout   │
│ - Visual Encoding   │
│ - Deterministic     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Flask Server        │
│ /api/snapshot       │
│ /api/node/<id>      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Three.js Frontend   │
│ - 3D Rendering      │
│ - Camera Controls   │
│ - Node Selection    │
└─────────────────────┘
```

## Features

### Visual Encodings

| **Attribute**     | **Encoding**                            | **Purpose**                |
|-------------------|-----------------------------------------|----------------------------|
| Position (x,y,z)  | 3D force-directed layout               | Semantic clustering        |
| Node Size         | Proportional to degree (0.5-2.5 units) | Connectivity importance    |
| Node Color        | Blue (atomic) / Gray (context)         | Node type identification   |
| Emissive Glow     | Based on degree                        | Hub detection              |
| Edge Opacity      | Scaled by weight (0.2-1.0)            | Relationship strength      |
| Edge Color        | Cyan/Red/White by type                 | Relationship type          |

### Deterministic Layout

- Same projection parameters → identical 3D positions
- Seed computed from: `hash(focus_node + threshold + depth)`
- 200 iterations of force-directed algorithm
- Repulsion (Coulomb's law) + Attraction (Hooke's law)

## Usage

### Quick Start

```bash
# 1. Install dependencies (if Flask not present)
pip install flask>=2.3.0

# 2. Start viewer for a projection
python src/visualization/server_3d.py projections/projection_1_t0.2_d1.json

# 3. Open browser
# http://127.0.0.1:8000
```

### Python API

```python
from src.visualization.server_3d import run_viewer_server

# Launch viewer
run_viewer_server(
    projection_path="projections/projection_1_t0.2_d1.json",
    port=8000
)
```

### Standalone Snapshot Export

```python
from src.visualization.snapshot_adapter_3d import convert_projection_to_3d_snapshot

# Convert projection to 3D snapshot JSON
convert_projection_to_3d_snapshot(
    projection_path="projections/projection_1_t0.2_d1.json",
    output_path="snapshots/projection_1_3d.json"
)
```

## Controls

| **Input**           | **Action**              |
|---------------------|-------------------------|
| Arrow Keys          | Rotate camera view      |
| Mouse Drag          | Pan camera              |
| Scroll Wheel        | Zoom in/out             |
| Click Node          | Show details panel      |

### Dynamic View Controls (Bottom Right Panel)

| **Control**         | **Function**            | **Range/Action** |
|---------------------|-------------------------|------------------|
| Label Detail (LOD)  | Adjust visible labels   | 5-100 labels     |
| Node Size Scale     | Scale all nodes         | 50%-200%         |
| Refresh View        | Reload from server      | Button           |
| Reset Camera        | Return to default view  | Button           |

## API Endpoints

### `GET /api/snapshot`
Returns complete 3D snapshot with nodes, edges, and metadata.

**Response:**
```json
{
  "nodes": [
    {
      "id": "atomic_28cf70b6fc7a9bce",
      "x": 12.34,
      "y": -5.67,
      "z": 8.90,
      "size": 1.5,
      "color": "#4A90E2",
      "label": "Neural networks are computational...",
      "node_type": "atomic",
      "degree": 8
    }
  ],
  "edges": [
    {
      "source": "atomic_28cf70b6fc7a9bce",
      "target": "atomic_25df1b32ffca1ea5",
      "weight": 0.625,
      "type": "related_to",
      "color": "#00AAFF"
    }
  ],
  "metadata": {
    "projection_parameters": {...},
    "layout_algorithm": "deterministic_force_3d",
    "layout_seed": 123456789,
    "node_count": 15,
    "edge_count": 42
  }
}
```

### `GET /api/node/<node_id>`
Returns detailed node information from original projection.

### `GET /api/health`
Health check endpoint.

## File Structure

```
viewer/
├── index.html              # Main HTML container
└── js/
    ├── main.js            # Application orchestrator
    ├── api.js             # API client
    ├── renderer.js        # Three.js setup
    ├── scene.js           # 3D geometry builder
    ├── input.js           # Camera controls
    ├── labels.js          # 2D label overlay
    └── ui.js              # UI panel management

src/visualization/
├── snapshot_adapter_3d.py  # Projection → 3D adapter
└── server_3d.py           # Flask server
```

## Constraints (from Specification)

✓ **Hard Constraint**: Projection JSON is never modified  
✓ **Hard Constraint**: Layout is deterministic for identical input  
✓ **Hard Constraint**: No similarity recomputation  

## Comparison Across Projections

The deterministic layout enables visual comparison:

- **threshold=0.2** → Dense connectivity, large clusters
- **threshold=0.7** → Sparse, isolated clusters
- **top_k=3** → Hub nodes clearly suppressed
- **depth=1** → Single-layer neighborhood
- **depth=5** → Deep cascading structure

Open multiple projections to compare topology differences.

## Performance

- **Label LOD**: Adjustable 5-100 labels (default 30)
- **Node Scaling**: Dynamic 50%-200% scaling
- **WebGL Rendering**: Hardware-accelerated
- **Raycasting**: Efficient node picking
- **Frustum Culling**: Labels only rendered when in view
- **Refresh**: Hot-reload without page refresh

## Dependencies

**Backend:**
- Python 3.9+
- Flask 2.3+
- Standard library (json, hashlib, math, random)

**Frontend:**
- Three.js r128 (CDN)
- Modern browser with WebGL support

## Success Criteria (per Specification)

✓ Different threshold/k combinations visibly alter topology  
✓ Hub suppression via top_k is visually obvious  
✓ High threshold isolates clusters  
✓ Rendering is identical across runs for same projection  

## Implementation Notes

### Force-Directed Algorithm

1. **Initialization**: Nodes distributed in sphere
2. **Repulsion**: Coulomb's law between all node pairs
3. **Attraction**: Hooke's law along edges (weighted)
4. **Velocity**: Verlet integration with damping
5. **Iterations**: 200 steps for convergence

### Visual Encoding Policy

Follows specification exactly:
- **atomic nodes**: Blue (#4A90E2)
- **context nodes**: Gray (#9B9B9B)
- **related_to edges**: Cyan (#00AAFF)
- **depends_on edges**: Red (#E74C3C)
- **appears_in edges**: White (#FFFFFF)

## Troubleshooting

**Issue**: Page loads but shows black screen  
**Solution**: Check browser console for Three.js errors. Ensure WebGL is supported.

**Issue**: Labels not appearing  
**Solution**: Labels use LOD - zoom closer to nodes or adjust `maxLabels` in labels.js

**Issue**: Server 404 on static files  
**Solution**: Ensure `viewer/` directory is at workspace root

**Issue**: Different positions on each load  
**Solution**: This indicates seed computation changed - verify projection parameters are identical

## License

See LICENSE file in project root.
