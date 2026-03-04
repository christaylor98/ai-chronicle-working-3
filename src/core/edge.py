"""
Edge types and relationship validation for the knowledge fabric.

Implements the strict relationship type system with validation rules.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

from src.core.node import Evidence


class EdgeType(str, Enum):
    """Allowed relationship types in the knowledge fabric."""
    
    # Weighted (continuous 0.0-1.0)
    RELATED_TO = "related_to"
    
    # Directed (boolean)
    DERIVED_FROM = "derived_from"
    REFINES = "refines"
    DEPENDS_ON = "depends_on"
    AUTHORED_BY = "authored_by"
    APPEARS_IN = "appears_in"


class EdgeCategory(str, Enum):
    """Edge semantic category."""
    
    WEIGHTED = "weighted"
    DIRECTED = "directed"


# Type metadata for validation
EDGE_METADATA = {
    EdgeType.RELATED_TO: {
        "category": EdgeCategory.WEIGHTED,
        "definition": "Continuous semantic similarity between atomic nodes",
        "requires_weight": True,
        "allowed_sources": ["atomic"],
        "allowed_targets": ["atomic"],
    },
    EdgeType.DERIVED_FROM: {
        "category": EdgeCategory.DIRECTED,
        "definition": "Target provides justification or origin of source",
        "requires_weight": False,
        "allowed_sources": ["atomic"],
        "allowed_targets": ["atomic"],
    },
    EdgeType.REFINES: {
        "category": EdgeCategory.DIRECTED,
        "definition": "Source narrows or specializes target",
        "requires_weight": False,
        "allowed_sources": ["atomic"],
        "allowed_targets": ["atomic"],
    },
    EdgeType.DEPENDS_ON: {
        "category": EdgeCategory.DIRECTED,
        "definition": "Source requires target to be valid or operational",
        "requires_weight": False,
        "allowed_sources": ["atomic"],
        "allowed_targets": ["atomic"],
    },
    EdgeType.AUTHORED_BY: {
        "category": EdgeCategory.DIRECTED,
        "definition": "Context node linked to author entity",
        "requires_weight": False,
        "allowed_sources": ["context"],
        "allowed_targets": ["atomic", "context"],
    },
    EdgeType.APPEARS_IN: {
        "category": EdgeCategory.DIRECTED,
        "definition": "Atomic node evidenced within context node",
        "requires_weight": False,
        "allowed_sources": ["atomic"],
        "allowed_targets": ["context"],
    },
}


class Edge(BaseModel):
    """
    Typed relationship between nodes.
    
    Validation rules:
    - Edge type matches allowed semantics
    - Direction is meaning-preserving
    - Edge has evidence pointer
    - Edge does not encode containment or hierarchy
    """
    
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    edge_type: EdgeType = Field(..., description="Relationship type")
    evidence: List[Evidence] = Field(default_factory=list, description="Justification for relationship")
    weight: Optional[float] = Field(None, ge=0.0, le=1.0, description="Weight for continuous edges")
    
    @field_validator("weight")
    @classmethod
    def validate_weight(cls, v: Optional[float], info) -> Optional[float]:
        """Ensure weight is present only for weighted edges."""
        edge_type = info.data.get("edge_type")
        if edge_type:
            metadata = EDGE_METADATA[edge_type]
            requires_weight = metadata["requires_weight"]
            
            if requires_weight and v is None:
                raise ValueError(f"Edge type {edge_type} requires a weight value")
            if not requires_weight and v is not None:
                raise ValueError(f"Edge type {edge_type} should not have a weight")
        
        return v
    
    @field_validator("edge_type")
    @classmethod
    def validate_no_containment(cls, v: EdgeType) -> EdgeType:
        """Prevent containment relationships."""
        # All allowed types are explicitly non-containment
        # This validator exists as a design assertion
        containment_types = ["contains", "has", "includes", "part_of"]
        if any(term in v.value for term in containment_types):
            raise ValueError(
                f"Containment relationships are prohibited. Found: {v}. "
                "Use 'appears_in' for evidence tracking only."
            )
        return v
    
    def validate_node_types(self, source_type: str, target_type: str) -> None:
        """Validate source and target node types against edge type constraints."""
        metadata = EDGE_METADATA[self.edge_type]
        
        if source_type not in metadata["allowed_sources"]:
            raise ValueError(
                f"Edge type {self.edge_type} does not allow source node type {source_type}. "
                f"Allowed: {metadata['allowed_sources']}"
            )
        
        if target_type not in metadata["allowed_targets"]:
            raise ValueError(
                f"Edge type {self.edge_type} does not allow target node type {target_type}. "
                f"Allowed: {metadata['allowed_targets']}"
            )
    
    def to_dict(self) -> dict:
        """Export to dict for JSON serialization."""
        result = {
            "source": self.source,
            "target": self.target,
            "type": self.edge_type.value,
            "evidence": [e.model_dump() for e in self.evidence],
        }
        if self.weight is not None:
            result["weight"] = self.weight
        return result


class WeightedEdge(BaseModel):
    """Specialized model for weighted edges (related_to)."""
    
    source: str
    target: str
    edge_type: EdgeType = Field(default=EdgeType.RELATED_TO, frozen=True)
    weight: float = Field(..., ge=0.0, le=1.0)
    
    def to_edge(self) -> Edge:
        """Convert to standard Edge model."""
        return Edge(
            source=self.source,
            target=self.target,
            edge_type=self.edge_type,
            weight=self.weight,
            evidence=[],
        )
    
    def to_dict(self) -> dict:
        """Export to dict for JSON serialization."""
        return {
            "source": self.source,
            "target": self.target,
            "type": self.edge_type.value,
            "weight": self.weight,
        }
