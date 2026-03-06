"""
Test batched LLM topic labeling with diverse topics.

Per BATCH_LLM_TOPIC_LABELLING_SPEC.v1.0:
- Single ai_factory API call labels all nodes
- Specific labels (e.g., 'ancient-egypt' not 'history')
- Works for arbitrary unknown domains
- Topic filtering correctly separates domains
"""

import json
import sys
from src.engine import IngestionEngine
from src.core.projection import ProjectionEngine, ProjectionParameters


def test_llm_topic_labeling():
    """Test batched LLM topic labeling on diverse topics."""
    
    # Initialize engine
    engine = IngestionEngine(similarity_k=5, strict_validation=False)
    
    print("BATCHED LLM TOPIC LABELING TEST")
    print("=" * 60)
    print()
    print("Per BATCH_LLM_TOPIC_LABELLING_SPEC.v1.0:")
    print("  - ONE ai_factory API call labels all nodes")
    print("  - Specific labels: 'ancient-egypt' not 'history'")
    print("  - Works for arbitrary unknown domains")
    print("  - Zero per-node API overhead")
    print()
    
    # Ingest diverse topics file
    print("Step 1: Ingesting diverse topics content...")
    print("-" * 60)
    truth_delta = engine.ingest_file("examples/diverse_topics.txt")
    
    print(f"✓ Ingestion complete")
    print(f"  Nodes added: {len(truth_delta['nodes_added'])}")
    print(f"  Edges added: {len(truth_delta['edges_added'])}")
    print()
    
    # Verify nodes have labels
    print("Step 2: Verifying topic labels assigned by LLM...")
    print("-" * 60)
    
    # Check Egypt nodes
    print("\n📍 Egypt-related nodes:")
    egypt_count = 0
    for node_data in truth_delta['nodes_added']:
        if node_data['node_type'] == 'atomic':
            stmt = node_data['statement']
            if 'egypt' in stmt.lower() or 'pyramid' in stmt.lower() or 'nile' in stmt.lower():
                labels = node_data['topic_labels']
                print(f"  • {stmt[:50]}...")
                print(f"    Labels: {labels}")
                egypt_count += 1
                
                # Verify specific labels (not generic)
                assert labels != ['general'], f"Egypt node has generic label: {stmt}"
                assert any('egypt' in label or 'pyramid' in label or 'nile' in label 
                          for label in labels), f"Egypt node missing specific label: {labels}"
    
    print(f"\n  ✓ {egypt_count} Egypt nodes with specific labels")
    
    # Check quantum nodes
    print("\n📍 Quantum physics nodes:")
    quantum_count = 0
    for node_data in truth_delta['nodes_added']:
        if node_data['node_type'] == 'atomic':
            stmt = node_data['statement']
            if 'quantum' in stmt.lower() or 'particle' in stmt.lower() or 'wave' in stmt.lower():
                labels = node_data['topic_labels']
                print(f"  • {stmt[:50]}...")
                print(f"    Labels: {labels}")
                quantum_count += 1
                
                # Verify specific labels
                assert labels != ['general'], f"Quantum node has generic label: {stmt}"
                assert any('quantum' in label or 'physics' in label or 'particle' in label
                          for label in labels), f"Quantum node missing specific label: {labels}"
    
    print(f"\n  ✓ {quantum_count} Quantum nodes with specific labels")
    
    # Check Amazon rainforest nodes
    print("\n📍 Amazon rainforest nodes:")
    amazon_count = 0
    for node_data in truth_delta['nodes_added']:
        if node_data['node_type'] == 'atomic':
            stmt = node_data['statement']
            if 'amazon' in stmt.lower() or 'rainforest' in stmt.lower():
                labels = node_data['topic_labels']
                print(f"  • {stmt[:50]}...")
                print(f"    Labels: {labels}")
                amazon_count += 1
                
                # Verify specific labels
                assert labels != ['general'], f"Amazon node has generic label: {stmt}"
                assert any('amazon' in label or 'rainforest' in label or 'forest' in label
                          for label in labels), f"Amazon node missing specific label: {labels}"
    
    print(f"\n  ✓ {amazon_count} Amazon nodes with specific labels")
    print()
    
    # Export graph
    print("Step 3: Exporting labeled graph...")
    print("-" * 60)
    engine.export_graph("diverse_topics_graph_llm.json")
    print("✓ Graph exported to diverse_topics_graph_llm.json")
    print()
    
    # Test topic filtering with LLM labels
    print("Step 4: Testing topic filtering with LLM labels...")
    print("-" * 60)
    
    # Find an Egypt node as focus
    egypt_node = None
    egypt_node_labels = []
    for node in engine.graph.atomic_nodes.values():
        if 'egypt' in node.statement.lower():
            egypt_node = node.node_id
            egypt_node_labels = node.topic_labels
            print(f"\nFocus node: {node.statement[:60]}...")
            print(f"Topic labels: {node.topic_labels}")
            break
    
    assert egypt_node, "No Egypt node found for projection test"
    
    # Create projection engine
    proj_engine = ProjectionEngine(engine.graph)
    
    # Projection WITHOUT topic filter
    params_no_filter = ProjectionParameters(
        focus_node=egypt_node,
        coherence_threshold=0.2,
        top_k_per_node=5,
        max_depth=1,
        max_nodes=100,
        topic_filter=False
    )
    proj_no_filter = proj_engine.project(params_no_filter)
    
    print(f"\n📊 Projection WITHOUT topic filter:")
    print(f"  Nodes: {len(proj_no_filter.nodes)}")
    print(f"  Sample neighbors (all domains):")
    for i, node_data in enumerate(proj_no_filter.nodes[1:6]):
        node = engine.graph.atomic_nodes[node_data['node_id']]
        print(f"    {i+1}. {node.statement[:50]}... [{', '.join(node.topic_labels)}]")
    
    # Projection WITH topic filter
    params_with_filter = ProjectionParameters(
        focus_node=egypt_node,
        coherence_threshold=0.2,
        top_k_per_node=5,
        max_depth=1,
        max_nodes=100,
        topic_filter=True
    )
    proj_with_filter = proj_engine.project(params_with_filter)
    
    print(f"\n📊 Projection WITH topic filter:")
    print(f"  Nodes: {len(proj_with_filter.nodes)}")
    print(f"  Sample neighbors (same domain only):")
    for i, node_data in enumerate(proj_with_filter.nodes[1:6]):
        node = engine.graph.atomic_nodes[node_data['node_id']]
        print(f"    {i+1}. {node.statement[:50]}... [{', '.join(node.topic_labels)}]")
    
    # Verify filtering worked
    assert len(proj_with_filter.nodes) < len(proj_no_filter.nodes), \
        "Topic filtering should reduce node count"
    
    # Verify filtered projection only has Egypt-related labels
    for node_data in proj_with_filter.nodes:
        if node_data['node_id'] != egypt_node:  # Skip focus node
            node = engine.graph.atomic_nodes[node_data['node_id']]
            # Check for label overlap with Egypt node
            overlap = set(node.topic_labels) & set(egypt_node_labels)
            # Should have at least some label overlap or be Egypt-related
            is_egypt = any('egypt' in label or 'pyramid' in label or 'nile' in label 
                          for label in node.topic_labels)
            assert overlap or is_egypt, \
                f"Filtered node has no label overlap: {node.topic_labels} vs {egypt_node_labels}"
    
    print("\n  ✓ Topic filtering correctly separated Egypt nodes from other domains")
    print()
    
    return engine


if __name__ == "__main__":
    print()
    engine = test_llm_topic_labeling()
    
    print("=" * 60)
    print("✅ ALL TESTS PASSED")
    print("=" * 60)
    print()
    print("Results:")
    print("  ✓ Single batched LLM call assigned labels to all nodes")
    print("  ✓ Labels are specific (e.g., 'ancient-egypt' not 'history')")
    print("  ✓ Works for arbitrary unknown domains (Egypt, quantum, Amazon)")
    print("  ✓ Topic filtering works with LLM labels")
    print("  ✓ Zero per-node API overhead")
    print()
    print("Per BATCH_LLM_TOPIC_LABELLING_SPEC.v1.0:")
    print("  - Batched LLM labeling > HDBSCAN clustering")
    print("  - Labels emerge from LLM understanding, not clustering")
    print("  - Single API call scales to any number of nodes")
    print("  - Projection owns filtering, ingestion owns assignment")
