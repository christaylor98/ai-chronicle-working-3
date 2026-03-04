# 3D Viewer - Dynamic Controls Update

## New Features Added

### 1. **Label Detail (LOD) Slider**
- **Range**: 5 to 100 labels
- **Default**: 30 labels
- **Purpose**: Dynamically adjust how many node labels are visible
- **Use cases**:
  - Performance tuning for large graphs
  - Reduce visual clutter
  - Focus on closest/most important nodes

**How to use:**
```
Drag the "Label Detail (LOD)" slider in the bottom-right panel
Value updates in real-time
More labels = more context but slower rendering
```

---

### 2. **Node Size Scale Slider**
- **Range**: 50% to 200%
- **Default**: 100%
- **Purpose**: Globally scale all node sizes
- **Use cases**:
  - Make small nodes more visible
  - Reduce overlap in dense graphs
  - Emphasize size-based encoding (degree)

**How to use:**
```
Drag the "Node Size Scale" slider
All nodes scale proportionally
Preserves relative size differences (degree encoding)
```

---

### 3. **Refresh View Button** (🔄)
- **Function**: Reload snapshot from server without page refresh
- **Preserves**:
  - Current camera position
  - Current zoom level
  - Current LOD and scale settings
- **Updates**:
  - Node positions (if projection changed)
  - Graph structure
  - Metadata display

**When to use:**
```
✓ Projection file was modified externally
✓ Server regenerated layout
✓ Want to see updated data without losing camera position
✓ Testing different projection parameters
```

**Behind the scenes:**
1. Calls `/api/snapshot/reload` to refresh server cache
2. Fetches new snapshot data
3. Rebuilds 3D scene
4. Reapplies current view settings

---

### 4. **Reset Camera Button** (📷)
- **Function**: Return camera to default viewing position
- **Resets**:
  - Position to (15, 15, 15)
  - Orientation to look at origin (0, 0, 0)
- **Preserves**:
  - LOD setting
  - Node scale
  - Scene data

**When to use:**
```
✓ Lost track of the graph while navigating
✓ Want to return to overview perspective
✓ After zooming into specific cluster
✓ Standardize view for screenshots/comparisons
```

---

## Updated UI Layout

```
┌────────────────────────────────────────────────┐
│  Info Panel         Canvas         Details     │
│  (top-left)         (center)       (top-right) │
│                                                 │
│                   [3D View]                     │
│                                                 │
│  Controls Help               View Controls     │
│  (bottom-left)               (bottom-right)    │
│  • Arrow keys                • LOD slider      │
│  • Mouse drag                • Scale slider    │
│  • Scroll                    • Refresh btn     │
│  • Click node                • Reset cam btn   │
└────────────────────────────────────────────────┘
```

---

## Implementation Details

### Files Modified

1. **viewer/index.html**
   - Added view controls panel HTML
   - Added sliders and buttons
   - Styled with matching theme

2. **viewer/js/ui.js**
   - Added `setupViewControls()` method
   - Added control event listeners
   - Added `setRefreshEnabled()` for button state

3. **viewer/js/main.js**
   - Added `setLabelLOD()` method
   - Added `setNodeScale()` method
   - Added `resetCamera()` method
   - Enhanced `reload()` to preserve settings

4. **viewer/js/scene.js**
   - Added `updateNodeScales()` method
   - Enhanced `highlightNode()` to respect scale
   - Added `baseScale` tracking in userData

### API Integration

The refresh button uses the existing `/api/snapshot/reload` endpoint:

```javascript
// Server-side (already existed)
@app.route("/api/snapshot/reload")
def reload_snapshot():
    """Force reload of snapshot data."""
    self.snapshot_cache = None
    self.adapter = ProjectionSnapshot3DAdapter(str(self.projection_path))
    return jsonify({"status": "reloaded"})
```

### State Management

```javascript
// Application state tracking
{
  snapshot: null,           // Current graph data
  selectedNodeId: null,     // Currently selected node
  nodeScaleFactor: 1.0,     // Current global scale
  initialCameraPosition: {  // Default camera pos
    x: 15, y: 15, z: 15
  }
}
```

---

## Usage Examples

### Scenario 1: Exploring a Large Graph

```
1. Load projection with many nodes
2. Reduce LOD to 10-15 labels (better performance)
3. Scale nodes down to 80% (reduce overlap)
4. Navigate with arrow keys and mouse
5. Click nodes to see details
6. Reset camera when needed
```

### Scenario 2: Comparing Projections

```
1. Open projection_1_t0.2_d1.json on port 8000
2. Note the camera position you like
3. Click Refresh to load updated data
4. Camera stays in same position
5. Visual comparison is easier
```

### Scenario 3: Presentation Mode

```
1. Set LOD to 50-60 (many labels visible)
2. Scale nodes up to 120% (more prominent)
3. Reset camera for consistent starting view
4. Navigate to show interesting clusters
5. Click nodes to explain details
```

### Scenario 4: Performance Tuning

```
If rendering is slow:
1. Reduce LOD to 5-10 labels
2. Scale nodes down to 70-80%
3. Close other browser tabs
4. Zoom out for overview

If too sparse:
1. Increase LOD to 80-100
2. Scale nodes up to 150-180%
3. Zoom in on clusters
```

---

## Benefits

### 1. **No Page Reload Required**
- All adjustments are instant
- State preserved during refresh
- Smooth exploration workflow

### 2. **Performance Adaptation**
- User can tune for their hardware
- Small graphs = max detail
- Large graphs = reduced detail

### 3. **Flexible Visualization**
- Same data, multiple perspectives
- Emphasis control via scaling
- Focus control via LOD

### 4. **Live Updates**
- Edit projection file
- Click refresh
- See changes immediately

---

## Testing

```bash
# Run automated tests
./test_viewer_features.sh

# Manual testing
./launch_viewer_3d.sh

# Then in browser:
1. Adjust LOD slider - verify label count changes
2. Adjust scale slider - verify nodes resize
3. Click refresh - verify data reloads
4. Navigate away - click reset camera - verify return
```

---

## Technical Notes

### LOD Implementation
```javascript
// Label manager filters by distance and limits count
labelDistances.sort((a, b) => a.distance - b.distance);
const visibleLabels = labelDistances
    .filter(l => l.inFrustum)
    .slice(0, this.maxLabels);  // Dynamic limit
```

### Scale Implementation
```javascript
// Global scale applied to all node meshes
for (const [nodeId, mesh] of this.sceneBuilder.nodeMeshes) {
    const nodeData = this.sceneBuilder.getNodeData(nodeId);
    const baseSize = nodeData.size;
    const newScale = baseSize * scale;
    mesh.scale.set(newScale, newScale, newScale);
}
```

### Refresh Implementation
```javascript
// Preserves state across reload
await fetch('/api/snapshot/reload');  // Server cache clear
this.sceneBuilder.clear();            // Remove old geometry
this.snapshot = await this.api.fetchSnapshot();  // Fetch new
this.sceneBuilder.buildFromSnapshot(this.snapshot);  // Rebuild
if (this.nodeScaleFactor !== 1.0) {
    this.setNodeScale(this.nodeScaleFactor);  // Reapply scale
}
```

---

## Future Enhancements

Potential additions:
- **Edge opacity slider** - Adjust relationship visibility
- **Color mode toggle** - Switch between encoding schemes
- **Animation speed** - Control rotation/transition speed
- **Snapshot presets** - Save/load view configurations
- **Export view** - Save current camera as image
- **Multi-projection** - Side-by-side comparison mode

---

## Summary

The 3D viewer now supports:
- ✓ **Dynamic LOD** (5-100 labels)
- ✓ **Node scaling** (50-200%)
- ✓ **Hot refresh** (no page reload)
- ✓ **Camera reset** (return to default)

All features work seamlessly with existing visualization system and preserve deterministic layout properties.

**Ready to use!** 🚀
