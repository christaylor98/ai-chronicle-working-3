"""
Main ingestion engine - orchestrates the complete pipeline.

Ingestion flow:
1. Parse input file into context node
2. Extract candidate atomic units
3. Validate atomicity
4. Create atomic nodes with evidence
5. Infer typed relationships
6. Validate connectivity
7. Output truth delta
"""

from typing import Optional, Dict, List
from pathlib import Path

from src.core import (
    AtomicNode,
    ContextNode,
    Candidate,
    Evidence,
    KnowledgeGraph,
    Edge,
    EdgeType,
)
from src.ingestion import (
    TextParser,
    AtomicityValidator,
    RelationshipBuilder,
)
from src.utils import SimilarityEngine, ProvenanceTracker


class IngestionEngine:
    """
    Orchestrates transformation of raw content into relational truth layer.
    
    Hard constraints enforced:
    - All nodes must be atomic or context
    - All edges must be typed
    - No orphaned nodes (or queued as candidates)
    - All assertions have provenance
    """
    
    def __init__(
        self,
        similarity_k: int = 10,
        strict_validation: bool = True,
    ):
        """
        Initialize ingestion engine.
        
        Per INGESTION_SIMILARITY_MEASUREMENT_SPEC.v1.0:
        - similarity_k is the top-K bound for related_to edges (default K=10)
        - NO semantic threshold filtering during ingestion
        - Similarity is MEASUREMENT, threshold is PROJECTION
        - Deduplication uses high threshold (0.85) to prevent duplicates
        
        Args:
            similarity_k: Maximum similar neighbors per node (default 10, bounded growth)
            strict_validation: Enable strict atomicity validation
        """
        self.similarity_k = similarity_k
        self.deduplication_threshold = 0.85  # High threshold for deduplication only
        
        # Initialize components
        self.parser = TextParser()
        self.validator = AtomicityValidator(strict=strict_validation)
        self.similarity_engine = SimilarityEngine()
        self.relationship_builder = RelationshipBuilder(self.similarity_engine)
        self.provenance = ProvenanceTracker()
        
        # Graph state
        self.graph = KnowledgeGraph()
    
    def ingest_file(
        self,
        file_path: str,
        author: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """
        Ingest a file into the knowledge graph.
        
        Args:
            file_path: Path to source file
            author: Optional author attribution
            metadata: Additional metadata for context node
        
        Returns:
            Truth delta (nodes_added, edges_added, etc.)
        """
        # Read file content
        content = self._read_file(file_path)
        
        # Create context node
        context_metadata = metadata or {}
        if author:
            context_metadata["author"] = author
        
        context_node = ContextNode.create(
            source_file=file_path,
            content=content,
            metadata=context_metadata
        )
        
        # Record provenance
        self.provenance.record_ingestion(
            context_node_id=context_node.node_id,
            source_file=file_path,
            metadata=context_metadata
        )
        
        # Add context node to graph
        self.graph.add_context_node(context_node)
        
        # Extract candidate atomic units
        extracted_units = self.parser.parse(content)
        
        # Validate and create atomic nodes
        atomic_nodes = []
        candidates = []
        
        for unit in extracted_units:
            # Validate atomicity
            is_valid, violations = self.validator.validate(unit.text)
            
            if not is_valid:
                # Queue as candidate with violations
                candidates.append(Candidate(
                    statement=unit.text,
                    reason="; ".join([v.description for v in violations]),
                    evidence=[Evidence(
                        source=context_node.node_id,
                        span=unit.span
                    )]
                ))
                continue
            
            # Check for similarity with existing nodes (deduplication)
            # Use higher threshold for deduplication to prevent true duplicates
            existing_statements = [node.statement for node in self.graph.atomic_nodes.values()]
            similar = self.similarity_engine.find_similar(
                unit.text,
                existing_statements,
                self.deduplication_threshold
            )
            
            if similar:
                # Skip - too similar to existing node
                continue
            
            # Create atomic node
            canonical_terms = self.parser.extract_key_terms(unit.text)
            evidence = Evidence(
                source=context_node.node_id,
                span=unit.span
            )
            
            atomic_node = AtomicNode.create(
                statement=unit.text,
                evidence=[evidence],
                canonical_terms=canonical_terms
            )
            
            atomic_nodes.append(atomic_node)
            self.graph.add_atomic_node(atomic_node)
        
        # Build relationships between nodes
        self._build_relationships(atomic_nodes, context_node.node_id)
        
        # Validate connectivity and queue orphans as candidates
        orphaned = self.graph.validate_connectivity()
        for orphan_id in orphaned:
            node = self.graph.atomic_nodes[orphan_id]
            candidates.append(Candidate(
                statement=node.statement,
                reason="Lacks connectivity to other nodes",
                evidence=node.evidence,
                proposed_node_id=orphan_id
            ))
        
        # Add candidates to graph
        for candidate in candidates:
            self.graph.add_candidate(candidate)
        
        # Generate truth delta
        truth_delta = self.graph.get_truth_delta()
        truth_delta["provenance"] = self.provenance.get_provenance()
        
        return truth_delta
    
    def _build_relationships(
        self,
        atomic_nodes: List[AtomicNode],
        context_node_id: str
    ) -> None:
        """Build all typed relationships for extracted nodes."""
        
        # 1. Build appears_in edges (evidence tracking)
        appears_in_edges = self.relationship_builder.build_appears_in_edges(
            atomic_nodes, context_node_id
        )
        for edge in appears_in_edges:
            self.graph.add_edge(edge)
        
        # 2. Build semantic similarity edges (related_to)
        # Use top-K measurement (no threshold filtering)
        similarity_edges = self.relationship_builder.build_similarity_edges(
            atomic_nodes,
            self.similarity_k
        )
        for edge in similarity_edges:
            self.graph.add_weighted_edge(edge)
        
        # 3. Infer derived_from relationships
        derived_edges = self.relationship_builder.infer_derived_from(atomic_nodes)
        for edge in derived_edges:
            try:
                self.graph.add_edge(edge)
            except ValueError:
                # Edge validation failed, skip
                pass
        
        # 4. Infer refines relationships
        refines_edges = self.relationship_builder.infer_refines(atomic_nodes)
        for edge in refines_edges:
            try:
                self.graph.add_edge(edge)
            except ValueError:
                pass
        
        # 5. Infer depends_on relationships
        depends_edges = self.relationship_builder.infer_depends_on(atomic_nodes)
        for edge in depends_edges:
            try:
                self.graph.add_edge(edge)
            except ValueError:
                pass
        
        # 6. Add authored_by edge if author present in context metadata
        context_node = self.graph.context_nodes[context_node_id]
        if "author" in context_node.metadata:
            # Note: Would need to create author node first in full implementation
            # For now, we document the relationship in metadata
            pass
    
    def _read_file(self, file_path: str) -> str:
        """Read file content with encoding handling."""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Try with different encoding
            return path.read_text(encoding="latin-1")
    
    def export_graph(self, output_path: str) -> None:
        """Export current graph state to JSON."""
        import json
        
        graph_data = self.graph.to_dict()
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(graph_data, f, indent=2, ensure_ascii=False)
    
    def export_truth_delta(self, output_path: str) -> None:
        """Export truth delta to JSON."""
        import json
        
        truth_delta = self.graph.get_truth_delta()
        truth_delta["provenance"] = self.provenance.get_provenance()
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(truth_delta, f, indent=2, ensure_ascii=False)
    
    def get_statistics(self) -> Dict:
        """Get ingestion statistics."""
        return {
            "atomic_nodes": len(self.graph.atomic_nodes),
            "context_nodes": len(self.graph.context_nodes),
            "edges": len(self.graph.edges),
            "weighted_edges": len(self.graph.weighted_edges),
            "candidates": len(self.graph.candidates),
            "orphaned_nodes": len(self.graph.validate_connectivity()),
        }
