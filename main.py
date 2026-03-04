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


def cmd_ingest(args):
    """Execute ingestion command."""
    print(f"Ingesting file: {args.input}")
    
    # Initialize engine
    engine = IngestionEngine(
        similarity_threshold=args.similarity_threshold,
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
        "-t", "--similarity-threshold",
        type=float,
        default=0.85,
        help="Similarity threshold for deduplication (default: 0.85)"
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


if __name__ == "__main__":
    main()
