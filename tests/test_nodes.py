"""
Test atomic node creation and validation.
"""

import pytest
from src.core.node import AtomicNode, ContextNode, Evidence


def test_atomic_node_creation():
    """Test creating an atomic node."""
    evidence = Evidence(source="test_context", span=(0, 50))
    
    node = AtomicNode.create(
        statement="Neural networks are computational models",
        evidence=[evidence],
        canonical_terms=["neural", "networks", "computational"]
    )
    
    assert node.node_id.startswith("atomic_")
    assert node.statement == "Neural networks are computational models"
    assert len(node.evidence) == 1
    assert node.stability_hash is not None


def test_atomic_node_rejects_pronoun_start():
    """Test that nodes starting with pronouns are rejected."""
    evidence = Evidence(source="test_context")
    
    with pytest.raises(ValueError, match="relies on external context"):
        AtomicNode.create(
            statement="This is a test statement",
            evidence=[evidence]
        )


def test_context_node_creation():
    """Test creating a context node."""
    context = ContextNode.create(
        source_file="test.txt",
        content="Test content",
        metadata={"author": "Test Author"}
    )
    
    assert context.node_id.startswith("context_")
    assert context.source_file == "test.txt"
    assert context.metadata["author"] == "Test Author"


def test_stability_hash_consistency():
    """Test that same statement produces same hash."""
    stmt = "Test statement for hashing"
    
    hash1 = AtomicNode.compute_stability_hash(stmt)
    hash2 = AtomicNode.compute_stability_hash(stmt)
    
    assert hash1 == hash2


def test_stability_hash_case_insensitive():
    """Test that hash is case-insensitive."""
    hash1 = AtomicNode.compute_stability_hash("Test Statement")
    hash2 = AtomicNode.compute_stability_hash("test statement")
    
    assert hash1 == hash2
