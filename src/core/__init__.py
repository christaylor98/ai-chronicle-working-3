"""Core package initialization."""

from src.core.node import AtomicNode, ContextNode, Candidate, Evidence, NodeType
from src.core.edge import Edge, WeightedEdge, EdgeType, EdgeCategory, EDGE_METADATA
from src.core.graph import KnowledgeGraph
from src.core.projection import (
    ProjectionEngine,
    ProjectionParameters,
    Projection,
    ProjectionMetadata,
    generate_perspective_suite,
)

__all__ = [
    "AtomicNode",
    "ContextNode",
    "Candidate",
    "Evidence",
    "NodeType",
    "Edge",
    "WeightedEdge",
    "EdgeType",
    "EdgeCategory",
    "EDGE_METADATA",
    "KnowledgeGraph",
    "ProjectionEngine",
    "ProjectionParameters",
    "Projection",
    "ProjectionMetadata",
    "generate_perspective_suite",
]
