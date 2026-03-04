"""
Test edge creation and validation.
"""

import pytest
from src.core.edge import Edge, WeightedEdge, EdgeType
from src.core.node import Evidence


def test_weighted_edge_creation():
    """Test creating a weighted edge."""
    edge = WeightedEdge(
        source="atomic_1",
        target="atomic_2",
        weight=0.85
    )
    
    assert edge.edge_type == EdgeType.RELATED_TO
    assert edge.weight == 0.85


def test_weighted_edge_requires_weight():
    """Test that weighted edges require weight parameter."""
    evidence = [Evidence(source="test")]
    
    with pytest.raises(ValueError, match="requires a weight"):
        Edge(
            source="atomic_1",
            target="atomic_2",
            edge_type=EdgeType.RELATED_TO,
            evidence=evidence
        )


def test_directed_edge_no_weight():
    """Test that directed edges should not have weight."""
    evidence = [Evidence(source="test")]
    
    with pytest.raises(ValueError, match="should not have a weight"):
        Edge(
            source="atomic_1",
            target="atomic_2",
            edge_type=EdgeType.DERIVED_FROM,
            weight=0.5,
            evidence=evidence
        )


def test_directed_edge_creation():
    """Test creating directed edges."""
    evidence = [Evidence(source="test")]
    
    edge = Edge(
        source="atomic_1",
        target="atomic_2",
        edge_type=EdgeType.DERIVED_FROM,
        evidence=evidence
    )
    
    assert edge.edge_type == EdgeType.DERIVED_FROM
    assert edge.weight is None


def test_appears_in_edge():
    """Test appears_in relationship."""
    evidence = [Evidence(source="context_1", span=(10, 50))]
    
    edge = Edge(
        source="atomic_1",
        target="context_1",
        edge_type=EdgeType.APPEARS_IN,
        evidence=evidence
    )
    
    assert edge.edge_type == EdgeType.APPEARS_IN
    assert edge.target == "context_1"
