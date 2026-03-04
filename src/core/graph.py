"""
Knowledge graph storage and management.

Maintains the truth layer with validation and query capabilities.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional, Set

from src.core.node import AtomicNode, ContextNode, Candidate, NodeType
from src.core.edge import Edge, EdgeType, WeightedEdge


class KnowledgeGraph:
    """
    Relational truth layer - sparse, precise, evidence-backed graph.
    
    Constraints enforced:
    - All nodes are atomic or context (no hierarchies)
    - All edges are typed and validated
    - No orphaned nodes (must have connectivity or be candidates)
    - All assertions have provenance
    """
    
    def __init__(self):
        self.atomic_nodes: Dict[str, AtomicNode] = {}
        self.context_nodes: Dict[str, ContextNode] = {}
        self.edges: List[Edge] = []
        self.weighted_edges: List[WeightedEdge] = []
        self.candidates: List[Candidate] = []
        
        # Adjacency tracking for connectivity validation
        self._adjacency: Dict[str, Set[str]] = defaultdict(set)
    
    def add_atomic_node(self, node: AtomicNode) -> None:
        """Add atomic node to graph."""
        if node.node_id in self.atomic_nodes:
            raise ValueError(f"Duplicate atomic node ID: {node.node_id}")
        
        self.atomic_nodes[node.node_id] = node
    
    def add_context_node(self, node: ContextNode) -> None:
        """Add context node to graph."""
        if node.node_id in self.context_nodes:
            raise ValueError(f"Duplicate context node ID: {node.node_id}")
        
        self.context_nodes[node.node_id] = node
    
    def add_edge(self, edge: Edge) -> None:
        """Add validated edge to graph."""
        # Validate nodes exist
        source_type = self._get_node_type(edge.source)
        target_type = self._get_node_type(edge.target)
        
        if source_type is None:
            raise ValueError(f"Source node {edge.source} does not exist")
        if target_type is None:
            raise ValueError(f"Target node {edge.target} does not exist")
        
        # Validate edge type constraints
        edge.validate_node_types(source_type, target_type)
        
        # Add to edge list and adjacency
        self.edges.append(edge)
        self._adjacency[edge.source].add(edge.target)
        self._adjacency[edge.target].add(edge.source)
    
    def add_weighted_edge(self, edge: WeightedEdge) -> None:
        """Add weighted relationship (related_to)."""
        # Validate both nodes are atomic
        if edge.source not in self.atomic_nodes:
            raise ValueError(f"Source node {edge.source} must be atomic")
        if edge.target not in self.atomic_nodes:
            raise ValueError(f"Target node {edge.target} must be atomic")
        
        self.weighted_edges.append(edge)
        self._adjacency[edge.source].add(edge.target)
        self._adjacency[edge.target].add(edge.source)
    
    def add_candidate(self, candidate: Candidate) -> None:
        """Queue candidate that lacks connectivity."""
        self.candidates.append(candidate)
    
    def _get_node_type(self, node_id: str) -> Optional[str]:
        """Determine node type by ID lookup."""
        if node_id in self.atomic_nodes:
            return "atomic"
        elif node_id in self.context_nodes:
            return "context"
        return None
    
    def get_connectivity(self, node_id: str) -> Set[str]:
        """Get all nodes connected to given node."""
        return self._adjacency.get(node_id, set())
    
    def get_orphaned_nodes(self) -> List[str]:
        """Find atomic nodes without any connections."""
        orphaned = []
        for node_id in self.atomic_nodes:
            if not self._adjacency.get(node_id):
                orphaned.append(node_id)
        return orphaned
    
    def validate_connectivity(self) -> List[str]:
        """
        Validate all atomic nodes have connectivity justification.
        
        Returns list of violations (orphaned node IDs).
        """
        return self.get_orphaned_nodes()
    
    def find_similar_nodes(self, statement: str, threshold: float = 0.85) -> List[str]:
        """
        Find existing nodes similar to statement (for deduplication).
        
        Returns list of node IDs above similarity threshold.
        """
        # Placeholder - will be implemented with semantic similarity
        # For now, use exact hash matching
        target_hash = AtomicNode.compute_stability_hash(statement)
        matches = []
        
        for node_id, node in self.atomic_nodes.items():
            if node.stability_hash == target_hash:
                matches.append(node_id)
        
        return matches
    
    def to_dict(self) -> dict:
        """Export complete graph state."""
        return {
            "atomic_nodes": {nid: node.to_dict() for nid, node in self.atomic_nodes.items()},
            "context_nodes": {nid: node.to_dict() for nid, node in self.context_nodes.items()},
            "edges": [e.to_dict() for e in self.edges],
            "weighted_edges": [e.to_dict() for e in self.weighted_edges],
            "candidates": [c.to_dict() for c in self.candidates],
        }
    
    def get_truth_delta(
        self, previous_state: Optional[KnowledgeGraph] = None
    ) -> dict:
        """
        Export truth delta (new additions since previous state).
        
        If no previous state, returns all current state as additions.
        """
        if previous_state is None:
            # All current state is new
            return {
                "nodes_added": [node.to_dict() for node in self.atomic_nodes.values()]
                             + [node.to_dict() for node in self.context_nodes.values()],
                "edges_added": [e.to_dict() for e in self.edges],
                "weights_added": [e.to_dict() for e in self.weighted_edges],
                "candidates": [c.to_dict() for c in self.candidates],
            }
        
        # Compute delta
        new_atomic = [
            node.to_dict()
            for nid, node in self.atomic_nodes.items()
            if nid not in previous_state.atomic_nodes
        ]
        new_context = [
            node.to_dict()
            for nid, node in self.context_nodes.items()
            if nid not in previous_state.context_nodes
        ]
        
        # Edge comparison by (source, target, type) tuple
        prev_edges = {(e.source, e.target, e.edge_type) for e in previous_state.edges}
        new_edges = [
            e.to_dict() for e in self.edges
            if (e.source, e.target, e.edge_type) not in prev_edges
        ]
        
        prev_weighted = {(e.source, e.target) for e in previous_state.weighted_edges}
        new_weighted = [
            e.to_dict() for e in self.weighted_edges
            if (e.source, e.target) not in prev_weighted
        ]
        
        return {
            "nodes_added": new_atomic + new_context,
            "edges_added": new_edges,
            "weights_added": new_weighted,
            "candidates": [c.to_dict() for c in self.candidates],
        }
