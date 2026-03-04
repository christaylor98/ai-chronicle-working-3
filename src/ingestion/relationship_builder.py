"""
Relationship inference and edge construction.
"""

from typing import List, Tuple
from src.core import AtomicNode, Edge, WeightedEdge, EdgeType, Evidence
from src.utils.similarity import SimilarityEngine


class RelationshipBuilder:
    """
    Infers typed relationships between atomic nodes.
    
    Relationship discovery strategies:
    - Semantic similarity → related_to (weighted)
    - Definitional patterns → derived_from, refines
    - Dependency patterns → depends_on
    - Evidence tracking → appears_in, authored_by
    """
    
    def __init__(self, similarity_engine: SimilarityEngine):
        self.similarity_engine = similarity_engine
    
    def build_similarity_edges(
        self,
        nodes: List[AtomicNode],
        threshold: float = 0.85
    ) -> List[WeightedEdge]:
        """
        Build related_to edges based on semantic similarity.
        
        Args:
            nodes: List of atomic nodes to compare
            threshold: Minimum similarity for edge creation
        
        Returns:
            List of weighted edges
        """
        edges = []
        
        if len(nodes) < 2:
            return edges
        
        # Extract statements
        statements = [node.statement for node in nodes]
        node_ids = [node.node_id for node in nodes]
        
        # Compute pairwise similarities
        similarities = self.similarity_engine.compute_pairwise_similarities(
            statements, threshold
        )
        
        # Create weighted edges
        for idx1, idx2, weight in similarities:
            edges.append(WeightedEdge(
                source=node_ids[idx1],
                target=node_ids[idx2],
                weight=weight
            ))
        
        return edges
    
    def infer_derived_from(
        self,
        nodes: List[AtomicNode]
    ) -> List[Edge]:
        """
        Infer derived_from relationships using textual patterns.
        
        Patterns indicating derivation:
        - "because", "since", "given that"
        - "follows from", "derived from"
        - References to prior statements
        """
        edges = []
        
        derivation_patterns = [
            "because", "since", "given that", "follows from",
            "derived from", "based on", "according to"
        ]
        
        for i, node in enumerate(nodes):
            statement_lower = node.statement.lower()
            
            # Check if this node references others
            for pattern in derivation_patterns:
                if pattern in statement_lower:
                    # Look for potential source nodes mentioned nearby
                    # Simple heuristic: check statements that appear earlier
                    for j in range(max(0, i - 3), i):
                        # If semantic similarity is high, create edge
                        similarity = self.similarity_engine.compute_similarity(
                            node.statement,
                            nodes[j].statement
                        )
                        
                        if similarity > 0.7:
                            edges.append(Edge(
                                source=node.node_id,
                                target=nodes[j].node_id,
                                edge_type=EdgeType.DERIVED_FROM,
                                evidence=[Evidence(
                                    source=node.evidence[0].source if node.evidence else "unknown",
                                    span=node.evidence[0].span if node.evidence else None
                                )]
                            ))
                            break  # Only one derivation source per pattern
        
        return edges
    
    def infer_refines(
        self,
        nodes: List[AtomicNode]
    ) -> List[Edge]:
        """
        Infer refines relationships (specialization).
        
        Patterns indicating refinement:
        - "specifically", "in particular", "more precisely"
        - Subsumption (statement contains another's key terms plus more specifics)
        """
        edges = []
        
        refinement_patterns = [
            "specifically", "in particular", "more precisely",
            "that is", "namely"
        ]
        
        for i, node in enumerate(nodes):
            statement_lower = node.statement.lower()
            
            for pattern in refinement_patterns:
                if pattern in statement_lower:
                    # Look for broader statement this might refine
                    for j, other_node in enumerate(nodes):
                        if i == j:
                            continue
                        
                        # Check if this node's terms are superset of other's
                        node_terms = set(node.canonical_terms)
                        other_terms = set(other_node.canonical_terms)
                        
                        if other_terms and other_terms.issubset(node_terms):
                            edges.append(Edge(
                                source=node.node_id,
                                target=other_node.node_id,
                                edge_type=EdgeType.REFINES,
                                evidence=[Evidence(
                                    source=node.evidence[0].source if node.evidence else "unknown"
                                )]
                            ))
                            break
        
        return edges
    
    def infer_depends_on(
        self,
        nodes: List[AtomicNode]
    ) -> List[Edge]:
        """
        Infer depends_on relationships (operational dependency).
        
        Patterns indicating dependency:
        - "requires", "needs", "depends on"
        - "assumes", "presupposes"
        """
        edges = []
        
        dependency_patterns = [
            "requires", "needs", "depends on", "relies on",
            "assumes", "presupposes", "contingent on"
        ]
        
        for i, node in enumerate(nodes):
            statement_lower = node.statement.lower()
            
            for pattern in dependency_patterns:
                if pattern in statement_lower:
                    # Look for nodes that might satisfy the dependency
                    for j, other_node in enumerate(nodes):
                        if i == j:
                            continue
                        
                        # Check if other node's terms appear after dependency keyword
                        pattern_pos = statement_lower.find(pattern)
                        after_pattern = statement_lower[pattern_pos:]
                        
                        # Simple heuristic: if other node's key term appears after pattern
                        if other_node.canonical_terms:
                            for term in other_node.canonical_terms:
                                if term.lower() in after_pattern:
                                    edges.append(Edge(
                                        source=node.node_id,
                                        target=other_node.node_id,
                                        edge_type=EdgeType.DEPENDS_ON,
                                        evidence=[Evidence(
                                            source=node.evidence[0].source if node.evidence else "unknown"
                                        )]
                                    ))
                                    break
        
        return edges
    
    def build_appears_in_edges(
        self,
        nodes: List[AtomicNode],
        context_node_id: str
    ) -> List[Edge]:
        """
        Create appears_in edges linking atomic nodes to their context.
        
        Args:
            nodes: Atomic nodes extracted from context
            context_node_id: ID of context node they appear in
        
        Returns:
            List of appears_in edges
        """
        edges = []
        
        for node in nodes:
            edges.append(Edge(
                source=node.node_id,
                target=context_node_id,
                edge_type=EdgeType.APPEARS_IN,
                evidence=node.evidence  # Use node's own evidence
            ))
        
        return edges
