"""
Test suite for visualization module.
"""

import json
import pytest
from pathlib import Path
from src.visualization import visualize_projection, ProjectionVisualizer, RenderConfig


def test_visualizer_loads_projection():
    """Test that visualizer correctly loads projection data."""
    proj_path = "projections/projection_1_t0.2_d1.json"
    if not Path(proj_path).exists():
        pytest.skip("Projection file not found")
    
    viz = ProjectionVisualizer(proj_path)
    
    assert viz.data is not None
    assert "nodes" in viz.data
    assert "edges" in viz.data
    assert "projection_parameters" in viz.data


def test_metrics_computation():
    """Test structural metrics computation."""
    proj_path = "projections/projection_1_t0.2_d1.json"
    if not Path(proj_path).exists():
        pytest.skip("Projection file not found")
    
    viz = ProjectionVisualizer(proj_path)
    
    assert viz.metrics.node_count > 0
    assert viz.metrics.edge_count >= 0
    assert viz.metrics.max_degree >= 0
    assert viz.metrics.average_degree >= 0
    assert isinstance(viz.metrics.degree_distribution, dict)


def test_sparse_vs_dense():
    """Test that high threshold produces sparse graph."""
    dense_path = "projections/projection_1_t0.2_d1.json"
    sparse_path = "projections/projection_7_t0.9_d1.json"
    
    if not Path(dense_path).exists() or not Path(sparse_path).exists():
        pytest.skip("Projection files not found")
    
    dense_viz = ProjectionVisualizer(dense_path)
    sparse_viz = ProjectionVisualizer(sparse_path)
    
    # Verify sparse has fewer edges than dense
    assert sparse_viz.metrics.edge_count < dense_viz.metrics.edge_count
    assert sparse_viz.metrics.average_degree <= dense_viz.metrics.average_degree


def test_deterministic_seed():
    """Test that seed computation is deterministic."""
    proj_path = "projections/projection_1_t0.2_d1.json"
    if not Path(proj_path).exists():
        pytest.skip("Projection file not found")
    
    viz1 = ProjectionVisualizer(proj_path)
    viz2 = ProjectionVisualizer(proj_path)
    
    assert viz1._compute_seed() == viz2._compute_seed()


def test_no_mutation():
    """Test that visualization does not mutate projection data."""
    proj_path = "projections/projection_1_t0.2_d1.json"
    if not Path(proj_path).exists():
        pytest.skip("Projection file not found")
    
    # Load original
    with open(proj_path) as f:
        original_data = json.load(f)
    
    # Visualize
    viz = ProjectionVisualizer(proj_path)
    
    # Reload
    with open(proj_path) as f:
        after_data = json.load(f)
    
    # Verify no mutation
    assert original_data == after_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
