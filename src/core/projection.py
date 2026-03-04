"""
Projection system for knowledge graph navigation.

PROJECTION_SYSTEM_SPEC.v1.0 - Reversible lens over immutable truth layer.

Hard constraints:
- MUST NOT mutate truth layer
- MUST NOT create new nodes or edges
- MUST NOT infer new relationships
- Filter related_to by coherence threshold only
- Directed edges always included if connected to included nodes
- Projection must be reproducible from truth layer + parameters
"""

from __future__ import annotations

from collections import deque
from typing import Dict, List, Set, Tuple, Optional
from pydantic import BaseModel, Field

from src.core.graph import KnowledgeGraph
from src.core.edge import EdgeType


class ProjectionParameters(BaseModel):
    """Parameters defining a projection lens over the truth layer."""
    
    focus_node: str = Field(..., description="Starting node ID for projection")
    coherence_threshold: float = Field(..., ge=0.0, le=1.0, description="Minimum weight for related_to edges")
    top_k_per_node: int = Field(default=5, ge=1, description="Maximum similarity edges per node (adaptive policy)")
    max_depth: int = Field(default=3, ge=1, description="Maximum hops from focus node")
    max_nodes: int = Field(default=100, ge=1, description="Maximum nodes to include")


class ProjectionMetadata(BaseModel):
    """Metadata about the generated projection."""
    
    node_count: int
    edge_count: int
    average_degree: float = Field(description="Average number of edges per node")
    density: float = Field(description="Ratio of actual edges to possible edges")


class Projection(BaseModel):
    """A filtered view of the knowledge graph from a specific perspective."""
    
    projection_parameters: ProjectionParameters
    nodes: List[Dict]
    edges: List[Dict]
    metadata: ProjectionMetadata


class ProjectionEngine:
    """
    Generate reversible projections over immutable truth layer.
    
    Projection is a lens, not a transformation:
    - No mutation of source graph
    - No creation of new relationships
    - No clustering or derived ontology
    - Pure filtering based on parameters
    """
    
    def __init__(self, knowledge_graph: KnowledgeGraph):
        """
        Initialize projection engine with truth layer.
        
        Args:
            knowledge_graph: Immutable truth layer to project from
        """
        self.graph = knowledge_graph
    
    def project(self, params: ProjectionParameters) -> Projection:
        """
        Generate a projection using specified parameters.
        
        Algorithm:
        1. Start from focus node
        2. Expand outward via BFS up to max_depth
        3. Filter related_to edges by coherence_threshold
        4. Always include directed edges if both endpoints included
        5. Respect max_nodes cap (highest weight first)
        
        Args:
            params: Projection parameters
        
        Returns:
            Projection containing filtered nodes and edges
        """
        # Validate focus node exists
        if not self._node_exists(params.focus_node):
            raise ValueError(f"Focus node {params.focus_node} does not exist in truth layer")
        
        # Stage 1: Discover nodes via BFS with threshold filtering
        included_nodes = self._discover_nodes(params)
        
        # Stage 2: Extract edges between included nodes using adaptive policy
        included_edges = self._extract_edges_adaptive(
            included_nodes, 
            params.coherence_threshold,
            params.top_k_per_node
        )
        
        # Stage 3: Serialize nodes to JSON-compatible format
        node_list = self._serialize_nodes(included_nodes)
        
        # Calculate metadata
        metadata = self._calculate_metadata(len(node_list), len(included_edges))
        
        return Projection(
            projection_parameters=params,
            nodes=node_list,
            edges=included_edges,
            metadata=metadata
        )
    
    def _node_exists(self, node_id: str) -> bool:
        """Check if node exists in truth layer."""
        return (node_id in self.graph.atomic_nodes or 
                node_id in self.graph.context_nodes)
    
    def _discover_nodes(self, params: ProjectionParameters) -> Set[str]:
        """
        Discover nodes via BFS from focus node.
        
        Respects max_depth and max_nodes constraints.
        Filters weighted edges by coherence threshold during expansion.
        """
        included = set()
        visited = set()
        queue = deque([(params.focus_node, 0)])  # (node_id, depth)
        
        # Track weighted edges for sorting by weight
        node_weights: Dict[str, float] = {params.focus_node: 1.0}
        
        while queue and len(included) < params.max_nodes:
            current_node, depth = queue.popleft()
            
            if current_node in visited:
                continue
            
            visited.add(current_node)
            included.add(current_node)
            
            # Don't expand beyond max_depth
            if depth >= params.max_depth:
                continue
            
            # Expand to neighbors via edges
            neighbors = self._get_neighbors(current_node, params.coherence_threshold)
            
            for neighbor, weight in neighbors:
                if neighbor not in visited:
                    # Track weight for prioritization
                    if neighbor not in node_weights:
                        node_weights[neighbor] = weight
                    else:
                        node_weights[neighbor] = max(node_weights[neighbor], weight)
                    
                    queue.append((neighbor, depth + 1))
        
        # If we exceeded max_nodes, keep the highest-weight nodes
        if len(included) > params.max_nodes:
            # Sort by weight descending, keeping focus node always
            sorted_nodes = sorted(
                [n for n in included if n != params.focus_node],
                key=lambda n: node_weights.get(n, 0.0),
                reverse=True
            )
            included = {params.focus_node}
            included.update(sorted_nodes[:params.max_nodes - 1])
        
        return included
    
    def _get_neighbors(
        self, 
        node_id: str, 
        coherence_threshold: float
    ) -> List[Tuple[str, float]]:
        """
        Get neighbors of a node with weights.
        
        - For weighted edges (related_to): filter by threshold
        - For directed edges: always include (weight = 1.0)
        """
        neighbors = []
        
        # Weighted edges (related_to) - apply threshold
        for wedge in self.graph.weighted_edges:
            if wedge.source == node_id and wedge.weight >= coherence_threshold:
                neighbors.append((wedge.target, wedge.weight))
            elif wedge.target == node_id and wedge.weight >= coherence_threshold:
                neighbors.append((wedge.source, wedge.weight))
        
        # Directed edges - always include (no threshold)
        for edge in self.graph.edges:
            if edge.source == node_id:
                neighbors.append((edge.target, 1.0))
            elif edge.target == node_id:
                neighbors.append((edge.source, 1.0))
        
        return neighbors
    
    def _extract_edges(
        self, 
        included_nodes: Set[str], 
        coherence_threshold: float
    ) -> List[Dict]:
        """
        Extract edges between included nodes.
        
        - Weighted edges: only if weight >= threshold
        - Directed edges: always included if both endpoints in projection
        """
        edges = []
        
        # Weighted edges (apply threshold)
        for wedge in self.graph.weighted_edges:
            if (wedge.source in included_nodes and 
                wedge.target in included_nodes and 
                wedge.weight >= coherence_threshold):
                edges.append({
                    "source": wedge.source,
                    "target": wedge.target,
                    "edge_type": wedge.edge_type,
                    "weight": wedge.weight,
                    "metadata": wedge.metadata
                })
        
        # Directed edges (no threshold, always include)
        for edge in self.graph.edges:
            if edge.source in included_nodes and edge.target in included_nodes:
                edges.append({
                    "source": edge.source,
                    "target": edge.target,
                    "edge_type": edge.edge_type,
                    "evidence": [e.model_dump() for e in edge.evidence]
                })
        
        return edges
    
    def _extract_edges_adaptive(
        self,
        included_nodes: Set[str],
        coherence_threshold: float,
        top_k_per_node: int
    ) -> List[Dict]:
        """
        Extract edges using ADAPTIVE_PROJECTION_POLICY.v1.0.
        
        Policy:
        1. Collect candidate related_to edges from each included node
        2. Filter by weight >= coherence_threshold
        3. Sort by weight DESC (deterministic: stable sort by weight DESC, node_id ASC)
        4. Select top_k_per_node edges for each node
        5. Union all selected edges
        6. Always include directed edges (appears_in, depends_on)
        
        Ensures:
        - Deterministic output (stable sort)
        - Per-node degree control (prevents mesh explosion)
        - Preserves structural edges (directed)
        - No mutation of truth layer
        """
        # Track selected edges to avoid duplicates (use frozenset for undirected nature)
        selected_edge_keys = set()
        edges = []
        
        # Step 1-5: Process similarity edges per node with adaptive policy
        # Sort included_nodes for deterministic iteration order
        for node_id in sorted(included_nodes):
            # Collect candidate edges from this node
            candidates = []
            
            for wedge in self.graph.weighted_edges:
                # Check if this edge connects to our node
                if wedge.source == node_id and wedge.target in included_nodes:
                    candidates.append((wedge.target, wedge.weight, wedge))
                elif wedge.target == node_id and wedge.source in included_nodes:
                    candidates.append((wedge.source, wedge.weight, wedge))
            
            # Step 2: Filter by threshold
            candidates = [(target, weight, wedge) for target, weight, wedge in candidates 
                         if weight >= coherence_threshold]
            
            # Step 3: Sort deterministically by (weight DESC, node_id ASC)
            # This ensures reproducible output even with tied weights
            candidates.sort(key=lambda x: (-x[1], x[0]))
            
            # Step 4: Select top_k_per_node
            selected = candidates[:top_k_per_node]
            
            # Step 5: Add to result set (avoid duplicates using edge key)
            for target, weight, wedge in selected:
                # Create canonical edge key (lower id first for undirected)
                edge_key = frozenset([wedge.source, wedge.target])
                
                if edge_key not in selected_edge_keys:
                    selected_edge_keys.add(edge_key)
                    edges.append({
                        "source": wedge.source,
                        "target": wedge.target,
                        "edge_type": wedge.edge_type,
                        "weight": wedge.weight,
                        "metadata": wedge.metadata
                    })
        
        # Step 6: Always include directed edges if both endpoints included
        for edge in self.graph.edges:
            if edge.source in included_nodes and edge.target in included_nodes:
                edges.append({
                    "source": edge.source,
                    "target": edge.target,
                    "edge_type": edge.edge_type,
                    "evidence": [e.model_dump() for e in edge.evidence]
                })
        
        # Sort edges for deterministic output (by source, then target)
        edges.sort(key=lambda e: (e["source"], e["target"]))
        
        return edges
    
    def _serialize_nodes(self, included_nodes: Set[str]) -> List[Dict]:
        """Serialize nodes to JSON-compatible format with deterministic ordering."""
        nodes = []
        
        # Sort node IDs for deterministic output
        for node_id in sorted(included_nodes):
            # Check atomic nodes
            if node_id in self.graph.atomic_nodes:
                node = self.graph.atomic_nodes[node_id]
                nodes.append({
                    "node_id": node.node_id,
                    "statement": node.statement,
                    "canonical_terms": node.canonical_terms,
                    "evidence": [e.model_dump() for e in node.evidence],
                    "node_type": node.node_type
                })
            
            # Check context nodes
            elif node_id in self.graph.context_nodes:
                node = self.graph.context_nodes[node_id]
                nodes.append({
                    "node_id": node.node_id,
                    "source_file": node.source_file,
                    "content_hash": node.content_hash,
                    "node_type": node.node_type,
                    "metadata": node.metadata
                })
        
        return nodes
    
    def _calculate_metadata(self, node_count: int, edge_count: int) -> ProjectionMetadata:
        """Calculate projection metadata including average degree."""
        # Average degree = 2 * edges / nodes (since each edge contributes to 2 nodes)
        average_degree = (2 * edge_count / node_count) if node_count > 0 else 0.0
        
        # Density = actual edges / possible edges
        # For undirected graph: possible = n * (n-1) / 2
        max_edges = (node_count * (node_count - 1)) / 2 if node_count > 1 else 1
        density = edge_count / max_edges if max_edges > 0 else 0.0
        
        return ProjectionMetadata(
            node_count=node_count,
            edge_count=edge_count,
            average_degree=round(average_degree, 2),
            density=round(density, 4)
        )


def generate_perspective_suite(
    knowledge_graph: KnowledgeGraph,
    focus_node: str
) -> List[Projection]:
    """
    Generate 7 standard projection perspectives over the truth layer.
    
    Uses ADAPTIVE_PROJECTION_POLICY.v1.0 with varying parameters:
    - Coherence thresholds: control semantic strength
    - Top-k per node: control degree/connectivity (prevents mesh explosion)
    - Depth: control exploration distance
    
    Variations explore different coherence thresholds, depths, and top-k:
    1. Low threshold (0.2), shallow depth (1), k=5 - immediate neighbors
    2. Low threshold (0.2), deep depth (5), k=3 - broad conceptual field (controlled)
    3. Medium threshold (0.5), shallow depth (1), k=5 - strong immediate connections
    4. Medium threshold (0.5), deep depth (3), k=4 - balanced exploration
    5. High threshold (0.7), shallow depth (2), k=3 - very strong local structure
    6. High threshold (0.7), deep depth (4), k=2 - strong extended network (sparse)
    7. Extreme threshold (0.9), atomic depth (1), k=2 - only atomic clarity
    
    Args:
        knowledge_graph: Truth layer to project from
        focus_node: Starting node for all projections
    
    Returns:
        List of 7 projections with varying parameters
    """
    engine = ProjectionEngine(knowledge_graph)
    
    perspectives = [
        # 1. Low threshold, shallow - see immediate context
        ProjectionParameters(
            focus_node=focus_node,
            coherence_threshold=0.2,
            top_k_per_node=5,
            max_depth=1,
            max_nodes=50
        ),
        
        # 2. Low threshold, deep - explore broad conceptual space (degree controlled)
        ProjectionParameters(
            focus_node=focus_node,
            coherence_threshold=0.2,
            top_k_per_node=3,
            max_depth=5,
            max_nodes=100
        ),
        
        # 3. Medium threshold, shallow - strong immediate connections
        ProjectionParameters(
            focus_node=focus_node,
            coherence_threshold=0.5,
            top_k_per_node=5,
            max_depth=1,
            max_nodes=30
        ),
        
        # 4. Medium threshold, deep - balanced navigation
        ProjectionParameters(
            focus_node=focus_node,
            coherence_threshold=0.5,
            top_k_per_node=4,
            max_depth=3,
            max_nodes=60
        ),
        
        # 5. High threshold, shallow - very strong local structure
        ProjectionParameters(
            focus_node=focus_node,
            coherence_threshold=0.7,
            top_k_per_node=3,
            max_depth=2,
            max_nodes=25
        ),
        
        # 6. High threshold, deep - strong extended network (sparse)
        ProjectionParameters(
            focus_node=focus_node,
            coherence_threshold=0.7,
            top_k_per_node=2,
            max_depth=4,
            max_nodes=50
        ),
        
        # 7. Extreme threshold - atomic clarity only
        ProjectionParameters(
            focus_node=focus_node,
            coherence_threshold=0.9,
            top_k_per_node=2,
            max_depth=1,
            max_nodes=15
        ),
    ]
    
    return [engine.project(params) for params in perspectives]
