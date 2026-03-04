# Projection System Example

## Overview
This example demonstrates the projection system's ability to generate multiple cognitive perspectives over an immutable truth layer.

## Truth Layer
File: `neural_networks_measured.json`
- 14 atomic nodes (neural network concepts)
- 1 context node (source doc)
- 79 weighted edges (related_to)
- 16 directed edges (appears_in, depends_on)

## Focus Node
`atomic_28cf70b6fc7a9bce`: "Neural networks are computational models inspired by biological neural systems"

## Generate Projections
```bash
python main.py project neural_networks_measured.json atomic_28cf70b6fc7a9bce
```

## Seven Perspectives

### Projection 1: Low Threshold (0.2), Shallow Depth (1)
- **Purpose**: Immediate neighborhood with weak connections
- **Result**: 15 nodes, 95 edges, density: 0.9048
- **Interpretation**: Broad conceptual field showing all semantic neighbors

### Projection 2: Low Threshold (0.2), Deep Depth (5)
- **Purpose**: Deep exploration of conceptual space
- **Result**: 15 nodes, 95 edges, density: 0.9048
- **Interpretation**: Full graph (all nodes reachable at low threshold)

### Projection 3: Medium Threshold (0.5), Shallow Depth (1)
- **Purpose**: Strong immediate connections only
- **Result**: 15 nodes, 95 edges, density: 0.9048
- **Interpretation**: Still includes most weighted edges

### Projection 4: Medium Threshold (0.5), Deep Depth (3)
- **Purpose**: Balanced navigation of the graph
- **Result**: 15 nodes, 95 edges, density: 0.9048
- **Interpretation**: Full exploration at medium confidence

### Projection 5: High Threshold (0.7), Shallow Depth (2)
- **Purpose**: Very strong local structure
- **Result**: 15 nodes, 16 edges, density: 0.1524
- **Interpretation**: Only typed directed edges remain (0 weighted edges)
- **Effect**: Shows structural backbone without semantic similarity

### Projection 6: High Threshold (0.7), Deep Depth (4)
- **Purpose**: Strong extended network
- **Result**: 15 nodes, 16 edges, density: 0.1524
- **Interpretation**: Same as #5 (no strong weighted edges exist)

### Projection 7: Extreme Threshold (0.9), Atomic Depth (1)
- **Purpose**: Atomic clarity only
- **Result**: 2 nodes, 1 edge, density: 1.0
- **Interpretation**: Minimal graph - focus node + context node
- **Effect**: Shows only direct evidence chain

## Key Observations

### Threshold Effects
- **0.2-0.5**: Includes most weighted edges (semantic similarity network)
- **0.7+**: Only directed edges (structural relationships)
- **0.9**: Minimal connected component

### Depth Effects
- All depths produce same result at low thresholds (graph is fully connected)
- Depth matters more in sparser projections

### Reversibility
Each projection can be regenerated from:
- Truth layer: `neural_networks_measured.json`
- Parameters: stored in projection file

### Immutability
- Truth layer file unchanged
- No clustering or derived ontology
- Pure filtering operation

## Use Cases

1. **Exploration** (Low threshold): Discover related concepts
2. **Navigation** (Medium threshold): Follow strong connections
3. **Verification** (High threshold): Examine structural relationships
4. **Inspection** (Extreme threshold): Trace evidence chain

## Files Generated
```
projections/
├── projection_1_t0.2_d1.json   # 36 KB - Full semantic network
├── projection_2_t0.2_d5.json   # 36 KB - Deep exploration
├── projection_3_t0.5_d1.json   # 36 KB - Medium threshold
├── projection_4_t0.5_d3.json   # 36 KB - Balanced navigation
├── projection_5_t0.7_d2.json   # 13 KB - Structural only
├── projection_6_t0.7_d4.json   # 13 KB - Extended structure
└── projection_7_t0.9_d1.json   # 1.3 KB - Atomic clarity
```

Note the dramatic file size reduction at high thresholds!

