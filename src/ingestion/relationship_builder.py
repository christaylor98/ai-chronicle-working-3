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
        k: int = 10
    ) -> List[WeightedEdge]:
        """
        Build related_to edges based on top-K semantic similarity.
        
        Per INGESTION_SIMILARITY_MEASUREMENT_SPEC.v1.0:
        - NO global threshold filtering during ingestion
        - Store top-K most similar neighbors per node (default K=10)
        - Preserve ALL measurements within bounded horizon
        - Threshold filtering belongs to projection layer, not ingestion
        - Symmetric edges (no duplicates)
        - Metadata includes similarity method only (no threshold)
        
        Philosophical shift:
        - Similarity is MEASUREMENT (stored in truth layer)
        - Threshold is PROJECTION (applied in query layer)
        - Ingestion MUST NOT apply semantic cutoffs
        
        Args:
            nodes: List of atomic nodes to compare
            k: Maximum number of neighbors to retain per node (bounded growth)
        
        Returns:
            List of weighted edges with similarity measurements
        """
        edges = []
        
        if len(nodes) < 2:
            return edges
        
        # Extract statements
        statements = [node.statement for node in nodes]
        node_ids = [node.node_id for node in nodes]
        
        # Compute top-K similarities (no threshold filtering)
        # This returns ALL top-K pairs, preserving measurement completeness
        similarities = self.similarity_engine.compute_topk_similarities(
            statements, k
        )
        
        # Determine similarity method
        method = "embedding_cosine" if self.similarity_engine._use_semantic else "basic_bow_cosine"
        
        # Create weighted edges with metadata (no threshold in metadata)
        for idx1, idx2, weight in similarities:
            edges.append(WeightedEdge(
                source=node_ids[idx1],
                target=node_ids[idx2],
                weight=weight,
                metadata={
                    "similarity_method": method,
                    "k": k,  # Document bounding parameter, not semantic cutoff
                    "measurement_type": "topk_similarity"
                }
            ))
        
        return edges
    
    def infer_derived_from(
        self,
        nodes: List[AtomicNode]
    ) -> List[Edge]:
        """
        Infer derived_from relationships using textual patterns.
        
        Per INGESTION_CORRECTION_SPEC.v1.0:
        - ONLY create when explicit lexical trigger present
        - Evidence MUST include non-null span
        - No implicit inference
        """
        edges = []
        
        # Strict lexical triggers
        derivation_patterns = [
            "derived from", "follows from", "based on"
        ]
        
        for i, node in enumerate(nodes):
            statement_lower = node.statement.lower()
            
            # Only proceed if explicit lexical trigger present
            trigger_found = False
            for pattern in derivation_patterns:
                if pattern in statement_lower:
                    trigger_found = True
                    break
            
            if not trigger_found:
                continue  # No lexical trigger, skip
            
            # Look for potential source nodes mentioned nearby
            for j in range(max(0, i - 3), i):
                # Check if target node's terms appear in source statement
                similarity = self.similarity_engine.compute_similarity(
                    node.statement,
                    nodes[j].statement
                )
                
                if similarity > 0.7:
                    # Only create if we have valid evidence span
                    if node.evidence and node.evidence[0].span:
                        edges.append(Edge(
                            source=node.node_id,
                            target=nodes[j].node_id,
                            edge_type=EdgeType.DERIVED_FROM,
                            evidence=[Evidence(
                                source=node.evidence[0].source,
                                span=node.evidence[0].span,
                                confidence=1.0
                            )]
                        ))
                    break
        
        return edges
    
    def infer_refines(
        self,
        nodes: List[AtomicNode]
    ) -> List[Edge]:
        """
        Infer refines relationships (specialization).
        
        Per INGESTION_CORRECTION_SPEC.v1.0:
        - ONLY create when explicit lexical trigger present
        - Evidence MUST include non-null span
        """
        edges = []
        
        # Strict lexical triggers
        refinement_patterns = [
            "more specifically", "in particular", "more precisely"
        ]
        
        for i, node in enumerate(nodes):
            statement_lower = node.statement.lower()
            
            # Only proceed if explicit lexical trigger present
            trigger_found = False
            for pattern in refinement_patterns:
                if pattern in statement_lower:
                    trigger_found = True
                    break
            
            if not trigger_found:
                continue  # No lexical trigger, skip
            
            # Look for broader statement this might refine
            for j, other_node in enumerate(nodes):
                if i == j:
                    continue
                
                # Check if this node's terms are superset of other's
                node_terms = set(node.canonical_terms)
                other_terms = set(other_node.canonical_terms)
                
                if other_terms and other_terms.issubset(node_terms):
                    # Only create if we have valid evidence span
                    if node.evidence and node.evidence[0].span:
                        edges.append(Edge(
                            source=node.node_id,
                            target=other_node.node_id,
                            edge_type=EdgeType.REFINES,
                            evidence=[Evidence(
                                source=node.evidence[0].source,
                                span=node.evidence[0].span,
                                confidence=1.0
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
        
        Per INGESTION_CORRECTION_SPEC.v1.0:
        - ONLY create edges when explicit lexical triggers present
        - Allowed triggers: 'depends on', 'requires', 'relies on'
        - Evidence MUST include non-null span
        """
        edges = []
        
        # STRICT lexical triggers only
        dependency_patterns = [
            "depends on", "requires", "relies on"
        ]
        
        for i, node in enumerate(nodes):
            statement_lower = node.statement.lower()
            
            # Only proceed if explicit lexical trigger present
            trigger_found = None
            trigger_pos = -1
            
            for pattern in dependency_patterns:
                if pattern in statement_lower:
                    trigger_found = pattern
                    trigger_pos = statement_lower.find(pattern)
                    break
            
            if not trigger_found:
                continue  # No lexical trigger, skip
            
            # Look for nodes that might satisfy the dependency
            for j, other_node in enumerate(nodes):
                if i == j:
                    continue
                
                # Check if other node's terms appear after dependency keyword
                after_pattern = statement_lower[trigger_pos:]
                
                # If other node's key term appears after trigger in source statement
                if other_node.canonical_terms:
                    for term in other_node.canonical_terms:
                        if term.lower() in after_pattern and len(term) > 3:
                            # Create edge with proper evidence span
                            if node.evidence and node.evidence[0].span:
                                edges.append(Edge(
                                    source=node.node_id,
                                    target=other_node.node_id,
                                    edge_type=EdgeType.DEPENDS_ON,
                                    evidence=[Evidence(
                                        source=node.evidence[0].source,
                                        span=node.evidence[0].span,  # Use actual span from source
                                        confidence=1.0
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
