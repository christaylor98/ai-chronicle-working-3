"""
Core data models for the relational knowledge fabric.

Defines atomic nodes, context nodes, and their validation rules.
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class Evidence(BaseModel):
    """Evidence pointer linking to source material."""
    
    source: str = Field(..., description="Context node ID or source identifier")
    span: Optional[tuple[int, int]] = Field(None, description="Character range in source [start, end)")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Extraction confidence")


class NodeType(str, Enum):
    """Node classification in the knowledge fabric."""
    
    ATOMIC = "atomic"
    CONTEXT = "context"


class AtomicNode(BaseModel):
    """
    Atomic semantic unit - smallest standalone coherent idea.
    
    Atomicity tests:
    1. Statement is self-contained
    2. Statement does not rely on external pronouns
    3. Statement expresses one claim
    4. Statement is not redundant with existing node above similarity threshold
    """
    
    node_id: str = Field(..., description="Unique identifier (generated)")
    statement: str = Field(..., min_length=10, description="Self-contained semantic unit")
    canonical_terms: List[str] = Field(default_factory=list, description="Key terms for indexing")
    evidence: List[Evidence] = Field(default_factory=list, min_length=1, description="Provenance chain")
    stability_hash: str = Field(..., description="Content-based hash for deduplication")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    node_type: NodeType = Field(default=NodeType.ATOMIC, frozen=True)
    
    @field_validator("statement")
    @classmethod
    def validate_atomicity(cls, v: str) -> str:
        """Basic atomicity checks on statement."""
        # Check for dependency pronouns that suggest non-self-containment
        dependency_patterns = ["this", "that", "it", "they", "these", "those"]
        words = v.lower().split()
        
        # Allow pronouns within compound sentences, but flag if statement starts with them
        if words and words[0] in dependency_patterns:
            raise ValueError(
                f"Statement appears to rely on external context (starts with '{words[0]}'). "
                "Atomic nodes must be self-contained."
            )
        
        return v
    
    @staticmethod
    def compute_stability_hash(statement: str) -> str:
        """Generate content-based hash for deduplication."""
        normalized = statement.strip().lower()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
    
    @classmethod
    def create(
        cls,
        statement: str,
        evidence: List[Evidence],
        canonical_terms: Optional[List[str]] = None,
    ) -> AtomicNode:
        """Factory method to create atomic node with auto-generated ID and hash."""
        stability_hash = cls.compute_stability_hash(statement)
        node_id = f"atomic_{stability_hash}"
        
        return cls(
            node_id=node_id,
            statement=statement,
            canonical_terms=canonical_terms or [],
            evidence=evidence,
            stability_hash=stability_hash,
        )
    
    def to_dict(self) -> dict:
        """Export to dict for JSON serialization."""
        return {
            "node_id": self.node_id,
            "statement": self.statement,
            "canonical_terms": self.canonical_terms,
            "evidence": [e.model_dump() for e in self.evidence],
            "stability_hash": self.stability_hash,
            "created_at": self.created_at.isoformat(),
            "node_type": self.node_type.value,
        }


class ContextNode(BaseModel):
    """
    Context node representing source file as evidence carrier.
    
    Does NOT contain other nodes - only provides context for appears_in relationships.
    """
    
    node_id: str = Field(..., description="Unique context identifier")
    source_file: str = Field(..., description="Original file path or URI")
    content_hash: str = Field(..., description="Hash of source content")
    metadata: dict = Field(default_factory=dict, description="Author, timestamp, etc.")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    node_type: NodeType = Field(default=NodeType.CONTEXT, frozen=True)
    
    @classmethod
    def create(cls, source_file: str, content: str, metadata: Optional[dict] = None) -> ContextNode:
        """Factory method to create context node."""
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
        node_id = f"context_{content_hash}"
        
        return cls(
            node_id=node_id,
            source_file=source_file,
            content_hash=content_hash,
            metadata=metadata or {},
        )
    
    def to_dict(self) -> dict:
        """Export to dict for JSON serialization."""
        return {
            "node_id": self.node_id,
            "source_file": self.source_file,
            "content_hash": self.content_hash,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "node_type": self.node_type.value,
        }


class Candidate(BaseModel):
    """
    Candidate node that lacks connectivity justification.
    
    Queued for human review or future relationship discovery.
    """
    
    statement: str
    reason: str = Field(..., description="Why this lacks connectivity")
    evidence: List[Evidence]
    proposed_node_id: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "statement": self.statement,
            "reason": self.reason,
            "evidence": [e.model_dump() for e in self.evidence],
            "proposed_node_id": self.proposed_node_id,
        }
