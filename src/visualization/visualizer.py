"""
Minimal projection visualization layer.
Pure rendering - no mutation of projection data.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Literal
from dataclasses import dataclass
from collections import Counter


@dataclass
class RenderConfig:
    """Visualization rendering configuration."""
    mode: Literal["static_png", "interactive_html"]
    layout: Literal["force", "circular"]
    output_path: Path


@dataclass
class GraphMetrics:
    """Derived structural metrics."""
    node_count: int
    edge_count: int
    degree_distribution: Dict[int, int]
    max_degree: int
    average_degree: float


class ProjectionVisualizer:
    """Deterministic structural visualization of projection output."""
    
    # Rendering policy constants
    NODE_COLORS = {"atomic": "#4A90E2", "context": "#9B9B9B"}
    EDGE_STYLES = {
        "related_to": {"color": "#CCCCCC", "width_scale": 2.0, "style": "solid"},
        "appears_in": {"color": "#000000", "width_scale": 1.0, "style": "solid"},
        "depends_on": {"color": "#E74C3C", "width_scale": 1.0, "style": "dashed"}
    }
    
    def __init__(self, projection_path: str):
        """Initialize with projection JSON path."""
        self.projection_path = Path(projection_path)
        self.data = self._load_projection()
        self.metrics = self._compute_metrics()
    
    def _load_projection(self) -> dict:
        """Load projection JSON without modification."""
        with open(self.projection_path, 'r') as f:
            return json.load(f)
    
    def _compute_metrics(self) -> GraphMetrics:
        """Compute structural metrics from projection data."""
        nodes = self.data.get("nodes", [])
        edges = self.data.get("edges", [])
        
        # Compute degree for each node
        degree_map = Counter()
        for edge in edges:
            degree_map[edge["source"]] += 1
            degree_map[edge["target"]] += 1
        
        # Degree distribution
        degree_dist = Counter(degree_map.values())
        
        # Metrics
        degrees = list(degree_map.values()) if degree_map else [0]
        return GraphMetrics(
            node_count=len(nodes),
            edge_count=len(edges),
            degree_distribution=dict(degree_dist),
            max_degree=max(degrees),
            average_degree=sum(degrees) / len(degrees) if degrees else 0.0
        )
    
    def render(self, config: RenderConfig) -> Path:
        """Render projection graph according to config."""
        if config.mode == "static_png":
            return self._render_static(config)
        else:
            return self._render_interactive(config)
    
    def _render_static(self, config: RenderConfig) -> Path:
        """Render static PNG using matplotlib and networkx."""
        import matplotlib.pyplot as plt
        import networkx as nx
        
        G = self._build_networkx_graph()
        
        # Deterministic layout with fixed seed
        seed = self._compute_seed()
        if config.layout == "force":
            pos = nx.spring_layout(G, seed=seed, k=1, iterations=50)
        else:
            pos = nx.circular_layout(G)
        
        fig, ax = plt.subplots(figsize=(16, 12))
        
        # Draw nodes by type
        for node_type, color in self.NODE_COLORS.items():
            nodelist = [n for n, d in G.nodes(data=True) if d.get("node_type") == node_type]
            sizes = [G.degree(n) * 100 + 200 for n in nodelist]
            nx.draw_networkx_nodes(G, pos, nodelist=nodelist, 
                                 node_color=color, node_size=sizes, 
                                 alpha=0.8, ax=ax)
        
        # Draw edges by type
        for edge_type, style in self.EDGE_STYLES.items():
            edgelist = [(u, v) for u, v, d in G.edges(data=True) if d.get("edge_type") == edge_type]
            widths = [G[u][v].get("weight", 0.5) * style["width_scale"] for u, v in edgelist]
            nx.draw_networkx_edges(G, pos, edgelist=edgelist,
                                 edge_color=style["color"], width=widths,
                                 style=style["style"], alpha=0.6, ax=ax)
        
        # Add title with metrics
        params = self.data.get("projection_parameters", {})
        title = (f"Projection: threshold={params.get('coherence_threshold', 'N/A')}, "
                f"depth={params.get('max_depth', 'N/A')}\n"
                f"Nodes: {self.metrics.node_count}, Edges: {self.metrics.edge_count}, "
                f"Max Degree: {self.metrics.max_degree}, Avg Degree: {self.metrics.average_degree:.2f}")
        ax.set_title(title, fontsize=12, pad=20)
        ax.axis("off")
        
        plt.tight_layout()
        plt.savefig(config.output_path, dpi=150, bbox_inches="tight")
        plt.close()
        
        return config.output_path
    
    def _render_interactive(self, config: RenderConfig) -> Path:
        """Render interactive HTML using pyvis."""
        from pyvis.network import Network
        
        # Create network with deterministic physics
        net = Network(height="900px", width="100%", bgcolor="#ffffff", 
                     font_color="black", directed=True)
        net.barnes_hut(gravity=-8000, central_gravity=0.3, 
                      spring_length=200, spring_strength=0.001,
                      damping=0.09)
        
        # Add nodes
        node_map = {}
        for node in self.data.get("nodes", []):
            node_id = node["node_id"]
            node_type = node.get("node_type", "atomic")
            
            if node_type == "atomic":
                label = node.get("statement", "")[:50] + "..."
            else:
                label = f"Context: {node.get('source_file', 'unknown')}"
            
            node_map[node_id] = node_type
            
            net.add_node(node_id, label=label, 
                        color=self.NODE_COLORS.get(node_type, "#999999"),
                        title=node.get("statement", "Context node"))
        
        # Add edges
        for edge in self.data.get("edges", []):
            source = edge["source"]
            target = edge["target"]
            edge_type = edge.get("edge_type", "related_to")
            weight = edge.get("weight", 0.5)
            
            style = self.EDGE_STYLES.get(edge_type, self.EDGE_STYLES["related_to"])
            
            net.add_edge(source, target, 
                        value=weight * style["width_scale"],
                        color=style["color"],
                        title=f"{edge_type}: {weight:.3f}")
        
        # Add metrics as text
        params = self.data.get("projection_parameters", {})
        net.heading = (f"Projection Visualization\n"
                      f"Threshold: {params.get('coherence_threshold', 'N/A')}, "
                      f"Depth: {params.get('max_depth', 'N/A')}, "
                      f"Nodes: {self.metrics.node_count}, "
                      f"Edges: {self.metrics.edge_count}")
        
        net.save_graph(str(config.output_path))
        return config.output_path
    
    def _build_networkx_graph(self):
        """Build NetworkX graph from projection data."""
        import networkx as nx
        
        G = nx.DiGraph()
        
        # Add nodes
        for node in self.data.get("nodes", []):
            G.add_node(node["node_id"], **node)
        
        # Add edges
        for edge in self.data.get("edges", []):
            G.add_edge(edge["source"], edge["target"], **edge)
        
        return G
    
    def _compute_seed(self) -> int:
        """Compute deterministic seed from projection path."""
        return int(hashlib.md5(str(self.projection_path).encode()).hexdigest()[:8], 16)
    
    def print_metrics(self):
        """Print structural metrics to stdout."""
        print(f"\n=== Projection Metrics: {self.projection_path.name} ===")
        print(f"Nodes: {self.metrics.node_count}")
        print(f"Edges: {self.metrics.edge_count}")
        print(f"Max Degree: {self.metrics.max_degree}")
        print(f"Average Degree: {self.metrics.average_degree:.2f}")
        print(f"\nDegree Distribution:")
        for degree in sorted(self.metrics.degree_distribution.keys()):
            count = self.metrics.degree_distribution[degree]
            print(f"  Degree {degree}: {count} nodes")
        
        params = self.data.get("projection_parameters", {})
        print(f"\nProjection Parameters:")
        for key, value in params.items():
            print(f"  {key}: {value}")
        print()


def visualize_projection(projection_path: str, 
                        mode: Literal["static_png", "interactive_html"] = "static_png",
                        layout: Literal["force", "circular"] = "force",
                        output_path: str = None) -> Tuple[Path, GraphMetrics]:
    """
    Main entry point for projection visualization.
    
    Args:
        projection_path: Path to projection JSON file
        mode: Rendering mode (static_png or interactive_html)
        layout: Graph layout algorithm (force or circular)
        output_path: Optional custom output path
    
    Returns:
        Tuple of (output_path, metrics)
    """
    visualizer = ProjectionVisualizer(projection_path)
    
    # Generate default output path if not provided
    if output_path is None:
        proj_name = Path(projection_path).stem
        ext = ".png" if mode == "static_png" else ".html"
        output_path = Path("visualizations") / f"{proj_name}_{layout}{ext}"
    else:
        output_path = Path(output_path)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Render
    config = RenderConfig(mode=mode, layout=layout, output_path=output_path)
    result_path = visualizer.render(config)
    
    # Print metrics
    visualizer.print_metrics()
    
    return result_path, visualizer.metrics
