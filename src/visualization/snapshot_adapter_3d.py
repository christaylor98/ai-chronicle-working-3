"""
PROJECTION_TO_3D_SNAPSHOT_ADAPTER.v1.0

Converts projection JSON into Three.js compatible 3D snapshot format.
Deterministic layout with no modification of source projection data.
"""

import json
import hashlib
import random
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
import math


@dataclass
class Node3D:
    """3D node representation for Three.js."""
    id: str
    x: float
    y: float
    z: float
    size: float
    color: str
    label: str
    node_type: str
    degree: int


@dataclass
class Edge3D:
    """3D edge representation for Three.js."""
    source: str
    target: str
    weight: float
    type: str


@dataclass
class Snapshot3D:
    """Complete 3D snapshot payload."""
    nodes: List[Dict]
    edges: List[Dict]
    metadata: Dict


class DeterministicForce3D:
    """
    Deterministic 3D force-directed layout algorithm.
    Identical input → identical output positions.
    """
    
    def __init__(self, seed: int, iterations: int = 200):
        self.seed = seed
        self.iterations = iterations
        self.k = 1.5  # Optimal distance
        self.c_rep = 1000  # Repulsion constant
        self.c_spring = 0.01  # Spring constant
        self.damping = 0.85  # Velocity damping
    
    def compute_layout(self, nodes: List[str], edges: List[Tuple[str, str, float]]) -> Dict[str, Tuple[float, float, float]]:
        """Compute 3D positions for nodes using force-directed algorithm."""
        # Initialize positions deterministically
        random.seed(self.seed)
        positions = {}
        velocities = {}
        
        for node_id in nodes:
            # Distribute nodes in a sphere initially
            theta = random.uniform(0, 2 * math.pi)
            phi = random.uniform(0, math.pi)
            r = 10.0
            
            x = r * math.sin(phi) * math.cos(theta)
            y = r * math.sin(phi) * math.sin(theta)
            z = r * math.cos(phi)
            
            positions[node_id] = [x, y, z]
            velocities[node_id] = [0.0, 0.0, 0.0]
        
        # Build adjacency for faster edge lookup
        adjacency = {node: [] for node in nodes}
        for source, target, weight in edges:
            adjacency[source].append((target, weight))
            adjacency[target].append((source, weight))
        
        # Force-directed iterations
        for iteration in range(self.iterations):
            forces = {node_id: [0.0, 0.0, 0.0] for node_id in nodes}
            
            # Repulsive forces (all pairs)
            for i, node_a in enumerate(nodes):
                for node_b in nodes[i+1:]:
                    pos_a = positions[node_a]
                    pos_b = positions[node_b]
                    
                    dx = pos_a[0] - pos_b[0]
                    dy = pos_a[1] - pos_b[1]
                    dz = pos_a[2] - pos_b[2]
                    
                    dist_sq = dx*dx + dy*dy + dz*dz + 0.01  # Avoid division by zero
                    dist = math.sqrt(dist_sq)
                    
                    # Coulomb's law
                    f_rep = self.c_rep / dist_sq
                    
                    fx = (dx / dist) * f_rep
                    fy = (dy / dist) * f_rep
                    fz = (dz / dist) * f_rep
                    
                    forces[node_a][0] += fx
                    forces[node_a][1] += fy
                    forces[node_a][2] += fz
                    
                    forces[node_b][0] -= fx
                    forces[node_b][1] -= fy
                    forces[node_b][2] -= fz
            
            # Attractive forces (edges only)
            for source, target, weight in edges:
                pos_s = positions[source]
                pos_t = positions[target]
                
                dx = pos_t[0] - pos_s[0]
                dy = pos_t[1] - pos_s[1]
                dz = pos_t[2] - pos_s[2]
                
                dist = math.sqrt(dx*dx + dy*dy + dz*dz + 0.01)
                
                # Hooke's law with weight scaling
                f_spring = self.c_spring * (dist - self.k) * weight
                
                fx = (dx / dist) * f_spring
                fy = (dy / dist) * f_spring
                fz = (dz / dist) * f_spring
                
                forces[source][0] += fx
                forces[source][1] += fy
                forces[source][2] += fz
                
                forces[target][0] -= fx
                forces[target][1] -= fy
                forces[target][2] -= fz
            
            # Update positions with velocity Verlet
            for node_id in nodes:
                velocities[node_id][0] = (velocities[node_id][0] + forces[node_id][0]) * self.damping
                velocities[node_id][1] = (velocities[node_id][1] + forces[node_id][1]) * self.damping
                velocities[node_id][2] = (velocities[node_id][2] + forces[node_id][2]) * self.damping
                
                positions[node_id][0] += velocities[node_id][0]
                positions[node_id][1] += velocities[node_id][1]
                positions[node_id][2] += velocities[node_id][2]
        
        # Convert to tuples
        return {node_id: tuple(pos) for node_id, pos in positions.items()}


class ProjectionSnapshot3DAdapter:
    """
    Converts projection JSON to Three.js 3D snapshot format.
    Preserves determinism and structural integrity.
    """
    
    # Rendering policy from specification
    NODE_COLORS = {
        "atomic": "#4A90E2",      # Blue
        "context": "#9B9B9B"      # Gray
    }
    
    EDGE_COLORS = {
        "related_to": "#00AAFF",   # Cyan
        "depends_on": "#E74C3C",   # Red
        "appears_in": "#FFFFFF"    # White
    }
    
    def __init__(self, projection_path: str):
        """Initialize adapter with projection JSON path."""
        self.projection_path = Path(projection_path)
        self.projection_data = self._load_projection()
    
    def _load_projection(self) -> dict:
        """Load projection JSON without any modification."""
        with open(self.projection_path, 'r') as f:
            return json.load(f)
    
    def _compute_seed(self) -> int:
        """Compute deterministic seed from projection parameters."""
        params = self.projection_data.get("projection_parameters", {})
        seed_string = f"{params.get('focus_node', '')}_{params.get('coherence_threshold', '')}_{params.get('max_depth', '')}"
        hash_obj = hashlib.sha256(seed_string.encode())
        return int(hash_obj.hexdigest()[:8], 16)
    
    def _compute_degree_map(self, edges: List[dict]) -> Dict[str, int]:
        """Compute node degree from edge list."""
        degree = {}
        for edge in edges:
            source = edge["source"]
            target = edge["target"]
            degree[source] = degree.get(source, 0) + 1
            degree[target] = degree.get(target, 0) + 1
        return degree
    
    def convert_to_snapshot(self) -> Snapshot3D:
        """
        Convert projection to 3D snapshot format.
        
        Returns deterministic 3D layout with visual encodings:
        - Position: 3D force-directed layout
        - Size: Proportional to node degree
        - Color: Based on node type (atomic/context)
        - Edge opacity: Scaled by weight
        """
        nodes = self.projection_data.get("nodes", [])
        edges = self.projection_data.get("edges", [])
        
        # Compute degree map
        degree_map = self._compute_degree_map(edges)
        
        # Prepare edge list for layout algorithm
        edge_tuples = [
            (e["source"], e["target"], e.get("weight", 0.5))
            for e in edges
        ]
        
        # Compute deterministic 3D layout
        node_ids = [n["node_id"] for n in nodes]
        seed = self._compute_seed()
        layout_engine = DeterministicForce3D(seed=seed, iterations=200)
        positions = layout_engine.compute_layout(node_ids, edge_tuples)
        
        # Build 3D nodes with visual encodings
        nodes_3d = []
        for node in nodes:
            node_id = node["node_id"]
            node_type = node.get("node_type", "atomic")
            degree = degree_map.get(node_id, 0)
            
            # Position from layout
            x, y, z = positions[node_id]
            
            # Size proportional to degree (0.5 to 2.5)
            size = 0.5 + (degree / 10.0) * 2.0
            size = min(size, 2.5)
            
            # Color by type
            color = self.NODE_COLORS.get(node_type, "#999999")
            
            # Label
            if node_type == "atomic":
                label = node.get("statement", "")[:40]
            else:
                label = f"Context: {node.get('source_file', 'unknown')}"
            
            nodes_3d.append({
                "id": node_id,
                "x": x,
                "y": y,
                "z": z,
                "size": size,
                "color": color,
                "label": label,
                "node_type": node_type,
                "degree": degree,
                "full_statement": node.get("statement", "") if node_type == "atomic" else None
            })
        
        # Build 3D edges
        edges_3d = []
        for edge in edges:
            edge_type = edge.get("edge_type", "related_to")
            edges_3d.append({
                "source": edge["source"],
                "target": edge["target"],
                "weight": edge.get("weight", 0.5),
                "type": edge_type,
                "color": self.EDGE_COLORS.get(edge_type, "#CCCCCC")
            })
        
        # Metadata from projection
        metadata = {
            "projection_parameters": self.projection_data.get("projection_parameters", {}),
            "layout_algorithm": "deterministic_force_3d",
            "layout_seed": seed,
            "node_count": len(nodes_3d),
            "edge_count": len(edges_3d),
            "max_degree": max(degree_map.values()) if degree_map else 0,
            "source_file": str(self.projection_path)
        }
        
        return Snapshot3D(
            nodes=[n for n in nodes_3d],
            edges=[e for e in edges_3d],
            metadata=metadata
        )
    
    def export_snapshot(self, output_path: str) -> Path:
        """Export snapshot to JSON file."""
        snapshot = self.convert_to_snapshot()
        
        output = {
            "nodes": snapshot.nodes,
            "edges": snapshot.edges,
            "metadata": snapshot.metadata
        }
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        
        return output_file


def convert_projection_to_3d_snapshot(projection_path: str, output_path: str) -> Path:
    """
    Convenience function to convert projection to 3D snapshot.
    
    Args:
        projection_path: Path to projection JSON file
        output_path: Path to write 3D snapshot JSON
    
    Returns:
        Path to created snapshot file
    """
    adapter = ProjectionSnapshot3DAdapter(projection_path)
    return adapter.export_snapshot(output_path)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python snapshot_adapter_3d.py <projection.json> <output_snapshot.json>")
        sys.exit(1)
    
    projection_file = sys.argv[1]
    output_file = sys.argv[2]
    
    result = convert_projection_to_3d_snapshot(projection_file, output_file)
    print(f"✓ Created 3D snapshot: {result}")
