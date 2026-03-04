#!/usr/bin/env python3
"""
Command-line interface for relational knowledge fabric ingestion system.

Usage:
    python main.py ingest <file> [options]
    python main.py validate <graph.json>
    python main.py stats <graph.json>
"""

import argparse
import json
import sys
from pathlib import Path

from src.engine import IngestionEngine
from src.core import (
    KnowledgeGraph,
    AtomicNode,
    ContextNode,
    Edge,
    WeightedEdge,
    generate_perspective_suite,
)


def cmd_ingest(args):
    """Execute ingestion command."""
    print(f"Ingesting file: {args.input}")
    
    # Initialize engine
    engine = IngestionEngine(
        similarity_k=args.similarity_k,
        strict_validation=not args.permissive,
    )
    
    # Ingest file
    try:
        truth_delta = engine.ingest_file(
            file_path=args.input,
            author=args.author,
            metadata={"description": args.description} if args.description else None,
        )
        
        # Export results
        output_path = args.output or f"{Path(args.input).stem}_graph.json"
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(truth_delta, f, indent=2, ensure_ascii=False)
        
        # Print statistics
        stats = engine.get_statistics()
        print(f"\nIngestion complete!")
        print(f"  Atomic nodes: {stats['atomic_nodes']}")
        print(f"  Context nodes: {stats['context_nodes']}")
        print(f"  Edges: {stats['edges']}")
        print(f"  Weighted edges: {stats['weighted_edges']}")
        print(f"  Candidates (issues): {stats['candidates']}")
        print(f"  Orphaned nodes: {stats['orphaned_nodes']}")
        print(f"\nOutput written to: {output_path}")
        
        # Warn if issues found
        if stats['candidates'] > 0:
            print(f"\n⚠ Warning: {stats['candidates']} statements failed atomicity validation")
            print("  Review 'candidates' section in output for details")
        
        if stats['orphaned_nodes'] > 0:
            print(f"\n⚠ Warning: {stats['orphaned_nodes']} nodes lack connectivity")
            print("  These are included in 'candidates' section")
    
    except Exception as e:
        print(f"Error during ingestion: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_validate(args):
    """Execute validation command."""
    print(f"Validating graph: {args.graph}")
    
    try:
        with open(args.graph, "r", encoding="utf-8") as f:
            graph_data = json.load(f)
        
        # Basic structure validation
        required_keys = ["nodes_added", "edges_added", "weights_added", "candidates"]
        missing = [key for key in required_keys if key not in graph_data]
        
        if missing:
            print(f"❌ Invalid graph structure. Missing keys: {missing}")
            sys.exit(1)
        
        # Count elements
        node_count = len(graph_data.get("nodes_added", []))
        edge_count = len(graph_data.get("edges_added", []))
        weight_count = len(graph_data.get("weights_added", []))
        candidate_count = len(graph_data.get("candidates", []))
        
        print(f"\n✓ Graph structure valid")
        print(f"  Nodes: {node_count}")
        print(f"  Edges: {edge_count}")
        print(f"  Weighted edges: {weight_count}")
        print(f"  Candidates: {candidate_count}")
        
        # Check for issues
        issues = []
        
        if candidate_count > node_count * 0.5:
            issues.append(f"High candidate ratio ({candidate_count}/{node_count})")
        
        if edge_count == 0 and node_count > 1:
            issues.append("No edges found (nodes are disconnected)")
        
        if issues:
            print(f"\n⚠ Validation warnings:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print(f"\n✓ No validation warnings")
    
    except FileNotFoundError:
        print(f"Error: File not found: {args.graph}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_stats(args):
    """Execute statistics command."""
    print(f"Analyzing graph: {args.graph}")
    
    try:
        with open(args.graph, "r", encoding="utf-8") as f:
            graph_data = json.load(f)
        
        nodes = graph_data.get("nodes_added", [])
        edges = graph_data.get("edges_added", [])
        weights = graph_data.get("weights_added", [])
        candidates = graph_data.get("candidates", [])
        
        # Compute statistics
        atomic_nodes = [n for n in nodes if n.get("node_type") == "atomic"]
        context_nodes = [n for n in nodes if n.get("node_type") == "context"]
        
        # Edge type distribution
        edge_types = {}
        for edge in edges:
            edge_type = edge.get("type", "unknown")
            edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
        
        # Print report
        print(f"\n{'='*60}")
        print(f"GRAPH STATISTICS")
        print(f"{'='*60}")
        print(f"\nNodes:")
        print(f"  Atomic nodes:  {len(atomic_nodes)}")
        print(f"  Context nodes: {len(context_nodes)}")
        print(f"  Total:         {len(nodes)}")
        
        print(f"\nRelationships:")
        print(f"  Directed edges:  {len(edges)}")
        print(f"  Weighted edges:  {len(weights)}")
        print(f"  Total:           {len(edges) + len(weights)}")
        
        print(f"\nEdge Type Distribution:")
        for edge_type, count in sorted(edge_types.items()):
            print(f"  {edge_type:20s} {count:5d}")
        
        print(f"\nQuality Metrics:")
        if len(atomic_nodes) > 0:
            avg_connectivity = (len(edges) + len(weights)) / len(atomic_nodes)
            print(f"  Avg connectivity:    {avg_connectivity:.2f} edges/node")
        
        candidate_ratio = len(candidates) / max(1, len(atomic_nodes))
        print(f"  Candidate ratio:     {candidate_ratio:.2%}")
        
        if weights:
            avg_weight = sum(w.get("weight", 0) for w in weights) / len(weights)
            print(f"  Avg similarity:      {avg_weight:.3f}")
        
        print(f"\n{'='*60}")
    
    except FileNotFoundError:
        print(f"Error: File not found: {args.graph}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_project(args):
    """Execute projection command."""
    print(f"Generating projections from: {args.graph}")
    print(f"Focus node: {args.focus}")
    
    try:
        # Load truth layer
        with open(args.graph, "r", encoding="utf-8") as f:
            graph_data = json.load(f)
        
        # Reconstruct knowledge graph
        kg = _reconstruct_graph(graph_data)
        
        # Validate focus node exists
        if not (args.focus in kg.atomic_nodes or args.focus in kg.context_nodes):
            print(f"❌ Error: Focus node '{args.focus}' not found in graph", file=sys.stderr)
            print(f"\nAvailable atomic nodes (showing first 10):")
            for i, node_id in enumerate(list(kg.atomic_nodes.keys())[:10]):
                node = kg.atomic_nodes[node_id]
                print(f"  {node_id}: {node.statement[:60]}...")
            sys.exit(1)
        
        # Generate projection suite
        print(f"\nGenerating 7 perspective projections...")
        projections = generate_perspective_suite(kg, args.focus)
        
        # Save each projection
        output_dir = Path(args.output_dir or "projections")
        output_dir.mkdir(exist_ok=True)
        
        for i, proj in enumerate(projections, 1):
            params = proj.projection_parameters
            filename = (
                f"projection_{i}_"
                f"t{params.coherence_threshold:.1f}_"
                f"d{params.max_depth}.json"
            )
            output_path = output_dir / filename
            
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(proj.model_dump(), f, indent=2, ensure_ascii=False)
            
            print(f"\n  [{i}/7] {filename}")
            print(f"       Threshold: {params.coherence_threshold:.1f}, "
                  f"Depth: {params.max_depth}, "
                  f"Max Nodes: {params.max_nodes}")
            print(f"       Result: {proj.metadata.node_count} nodes, "
                  f"{proj.metadata.edge_count} edges, "
                  f"density: {proj.metadata.density:.4f}")
        
        print(f"\n✓ All projections saved to: {output_dir}/")
        print(f"\nProjection suite demonstrates:")
        print(f"  • Low threshold → broader conceptual field")
        print(f"  • High threshold → atomic precision")
        print(f"  • Shallow depth → local neighborhood")
        print(f"  • Deep depth → extended network")
        print(f"\nAll projections are reversible lenses over the immutable truth layer.")
    
    except FileNotFoundError:
        print(f"Error: File not found: {args.graph}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error during projection: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def _reconstruct_graph(graph_data: dict) -> KnowledgeGraph:
    """Reconstruct KnowledgeGraph from JSON truth delta."""
    from src.core.node import Evidence
    from datetime import datetime
    
    kg = KnowledgeGraph()
    
    # Add nodes
    for node_data in graph_data.get("nodes_added", []):
        node_type = node_data.get("node_type")
        
        if node_type == "atomic":
            # Reconstruct evidence
            evidence = [
                Evidence(**ev) for ev in node_data.get("evidence", [])
            ]
            
            # Parse datetime
            created_at = node_data.get("created_at")
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            
            node = AtomicNode(
                node_id=node_data["node_id"],
                statement=node_data["statement"],
                canonical_terms=node_data.get("canonical_terms", []),
                evidence=evidence,
                stability_hash=node_data["stability_hash"],
                created_at=created_at,
            )
            kg.add_atomic_node(node)
        
        elif node_type == "context":
            node = ContextNode(
                node_id=node_data["node_id"],
                source_file=node_data["source_file"],
                content_hash=node_data["content_hash"],
                metadata=node_data.get("metadata", {}),
            )
            kg.add_context_node(node)
    
    # Add edges
    for edge_data in graph_data.get("edges_added", []):
        evidence = [Evidence(**ev) for ev in edge_data.get("evidence", [])]
        
        edge = Edge(
            source=edge_data["source"],
            target=edge_data["target"],
            edge_type=edge_data["type"],  # Note: JSON uses "type" not "edge_type"
            evidence=evidence,
        )
        kg.add_edge(edge)
    
    # Add weighted edges
    for wedge_data in graph_data.get("weights_added", []):
        wedge = WeightedEdge(
            source=wedge_data["source"],
            target=wedge_data["target"],
            weight=wedge_data["weight"],
            metadata=wedge_data.get("metadata", {}),
        )
        kg.add_weighted_edge(wedge)
    
    return kg


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Relational Knowledge Fabric Ingestion System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest file into knowledge graph")
    ingest_parser.add_argument("input", help="Input file to ingest")
    ingest_parser.add_argument("-o", "--output", help="Output JSON file")
    ingest_parser.add_argument("-a", "--author", help="Author attribution")
    ingest_parser.add_argument("-d", "--description", help="File description")
    ingest_parser.add_argument(
        "-k", "--similarity-k",
        type=int,
        default=10,
        help="Top-K similar neighbors per node (default: 10, per MEASUREMENT_SPEC v1.0)"
    )
    ingest_parser.add_argument(
        "-p", "--permissive",
        action="store_true",
        help="Disable strict atomicity validation"
    )
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate graph structure")
    validate_parser.add_argument("graph", help="Graph JSON file to validate")
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show graph statistics")
    stats_parser.add_argument("graph", help="Graph JSON file to analyze")
    
    # Project command
    project_parser = subparsers.add_parser(
        "project", 
        help="Generate projection perspectives over truth layer"
    )
    project_parser.add_argument("graph", help="Graph JSON file (truth layer)")
    project_parser.add_argument("focus", help="Focus node ID to start projection from")
    project_parser.add_argument(
        "-o", "--output-dir",
        help="Output directory for projections (default: ./projections)"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Dispatch command
    if args.command == "ingest":
        cmd_ingest(args)
    elif args.command == "validate":
        cmd_validate(args)
    elif args.command == "stats":
        cmd_stats(args)
    elif args.command == "project":
        cmd_project(args)


if __name__ == "__main__":
    main()
