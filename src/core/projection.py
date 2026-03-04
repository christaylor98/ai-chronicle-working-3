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
    max_depth: int = Field(default=3, ge=1, description="Maximum hops from focus node")
    max_nodes: int = Field(default=100, ge=1, description="Maximum nodes to include")


class ProjectionMetadata(BaseModel):
    """Metadata about the generated projection."""
    
    node_count: int
    edge_count: int
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
        
        # Stage 2: Extract edges between included nodes
        included_edges = self._extract_edges(included_nodes, params.coherence_threshold)
        
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
    
    def _serialize_nodes(self, included_nodes: Set[str]) -> List[Dict]:
        """Serialize nodes to JSON-compatible format."""
        nodes = []
        
        for node_id in included_nodes:
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
        """Calculate projection metadata."""
        # Density = actual edges / possible edges
        # For undirected graph: possible = n * (n-1) / 2
        max_edges = (node_count * (node_count - 1)) / 2 if node_count > 1 else 1
        density = edge_count / max_edges if max_edges > 0 else 0.0
        
        return ProjectionMetadata(
            node_count=node_count,
            edge_count=edge_count,
            density=round(density, 4)
        )


def generate_perspective_suite(
    knowledge_graph: KnowledgeGraph,
    focus_node: str
) -> List[Projection]:
    """
    Generate 7 standard projection perspectives over the truth layer.
    
    Variations explore different coherence thresholds and depths:
    1. Low threshold (0.2), shallow depth (1) - immediate neighbors
    2. Low threshold (0.2), deep depth (5) - broad conceptual field
    3. Medium threshold (0.5), shallow depth (1) - strong immediate connections
    4. Medium threshold (0.5), deep depth (3) - balanced exploration
    5. High threshold (0.7), shallow depth (2) - very strong local structure
    6. High threshold (0.7), deep depth (4) - strong extended network
    7. Extreme threshold (0.9), atomic depth (1) - only atomic clarity
    
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
            max_depth=1,
            max_nodes=50
        ),
        
        # 2. Low threshold, deep - explore broad conceptual space
        ProjectionParameters(
            focus_node=focus_node,
            coherence_threshold=0.2,
            max_depth=5,
            max_nodes=100
        ),
        
        # 3. Medium threshold, shallow - strong immediate connections
        ProjectionParameters(
            focus_node=focus_node,
            coherence_threshold=0.5,
            max_depth=1,
            max_nodes=30
        ),
        
        # 4. Medium threshold, deep - balanced navigation
        ProjectionParameters(
            focus_node=focus_node,
            coherence_threshold=0.5,
            max_depth=3,
            max_nodes=60
        ),
        
        # 5. High threshold, shallow - very strong local structure
        ProjectionParameters(
            focus_node=focus_node,
            coherence_threshold=0.7,
            max_depth=2,
            max_nodes=25
        ),
        
        # 6. High threshold, deep - strong extended network
        ProjectionParameters(
            focus_node=focus_node,
            coherence_threshold=0.7,
            max_depth=4,
            max_nodes=50
        ),
        
        # 7. Extreme threshold - atomic clarity only
        ProjectionParameters(
            focus_node=focus_node,
            coherence_threshold=0.9,
            max_depth=1,
            max_nodes=15
        ),
    ]
    
    return [engine.project(params) for params in perspectives]
