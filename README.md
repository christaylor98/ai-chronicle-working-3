# Relational Knowledge Fabric Ingestion System

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-See%20LICENSE-green.svg)](LICENSE)
[![Specification](https://img.shields.io/badge/spec-v1.0%20Full-brightgreen.svg)](SPECIFICATION.md)

**Version**: 1.0.0 + CORRECTION_SPEC v1.0 + MEASUREMENT_SPEC v1.0 + PROJECTION_SPEC v1.0  
**Specification**: INGESTION_SYSTEM_SPEC.v1.0 + CORRECTION + MEASUREMENT + PROJECTION  
**Status**: ✅ Production Ready - Hardened + Measurement-Complete + Projection-Enabled

## Overview

A rigorous ingestion system that compiles unstructured content into a relational knowledge graph composed of:
- **Atomic nodes**: Self-contained, minimal semantic units
- **Typed relationships**: Precise directional or weighted connections
- **Context nodes**: Source files as evidence carriers
- **Provenance tracking**: Full evidence chain for all assertions

## Core Principles

1. **Relational truth is primary** - No hierarchies or ontological containment
2. **Ingestion is compilation** - Not interpretation or summarization
3. **Atomic units must earn their keep** - Every node must justify connectivity
4. **Constraint > Priority > Goal** - Hard limits are inviolable
5. **Reversibility guaranteed** - Append-only operations with full evidence trails

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/christaylor98/ai-chronicle-working-3.git
cd ai-chronicle-working-3

# Install dependencies
pip install -r requirements.txt

# Note: See INSTALL.md for dependency troubleshooting
```

### Basic Usage

```bash
# Ingest a file
python main.py ingest examples/neural_networks.txt

# With metadata
python main.py ingest input.txt --author "John Doe" --output graph.json

# Validate output
python main.py validate graph.json

# Analyze statistics
python main.py stats graph.json

# Generate projection perspectives
python main.py project graph.json <focus_node_id>
```

### Python API

```python
from src.engine import IngestionEngine

# Initialize engine
engine = IngestionEngine(similarity_threshold=0.85)

# Ingest file
truth_delta = engine.ingest_file(
    "input.txt",
    author="John Doe",
    metadata={"domain": "machine_learning"}
)

# Export results
engine.export_truth_delta("output.json")
```

## Architecture
, projection
```
src/
├── core/           # Data models (nodes, edges, graph)
├── ingestion/      # Extraction, validation, relationship building
├── utils/          # Hashing, similarity, evidence tracking
└── engine.py       # Main ingestion orchestrator
```

## Output Format

The system produces a truth delta containing:

```json
{
  "nodes_added": [
    {
      "node_id": "atomic_abc123",
      "statement": "Self-contained semantic unit",
      "canonical_terms": ["term1", "term2"],
      "evidence": [{"source": "doc_xyz", "span": [10, 45]}],
      "stability_hash": "sha256:..."
    }
  ],
  "edges_added": [
    {
      "source": "node1",
      "target": "node2",
      "type": "derived_from",
      "evidence": [...]
    }
  ],
  "weights_added": [
    {
      "source": "node1",
      "target": "node2",
      "type": "related_to",
      "weight": 0.87
    }
  ],
  "candidates": [...],
  "provenance": [...]
}
```

## Relationship Types

### Weighted (Continuous 0.0-1.0)
- **related_to**: Semantic similarity between atomic nodes

### Directed (Boolean)
- **derived_from**: Target provides justification/origin of source
- **refines**: Source narrows or specializes target
- **depends_on**: Source requires target to be valid
- **authored_by**: Context node linked to author entity
- **appears_in**: Atomic node evidenced within context node

## Hard Constraints

1. Truth layer consists ONLY of atomic nodes and typed relationships
2. Documents are context nodes, NOT containers
3. All atomic nodes must be self-contained and minimally sufficient
4. Every node must connect to at least one other node or be queued as candidate
5. Every relationship must match an allowed type exactly
6. No implicit merging, clustering, summarizing, or abstraction
7. All nodes and edges must include evidence provenance

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)**: 5-minute getting started guide
- **[INSTALL.md](INSTALL.md)**: Complete installation guide with dependency troubleshooting
- **[USAGE.md](USAGE.md)**: Comprehensive usage guide with examples and best practices
- **[SPECIFICATION.md](SPECIFICATION.md)**: Formal specification (BASE + CORRECTION + MEASUREMENT)
- **[CORRECTION_SUMMARY.md](CORRECTION_SUMMARY.md)**: Hardening corrections and verification
- **[ENRICHMENT_SUMMARY.md](ENRICHMENT_SUMMARY.md)**: Relational enrichment implementation and analysis
- **[MEASUREMENT_SUMMARY.md](MEASUREMENT_SUMMARY.md)**: Top-K measurement architecture (supersedes enrichment)
- **[PROJECTION_SUMMARY.md](PROJECTION_SUMMARY.md)**: Projection system for cognitive navigation over truth layer
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)**: Technical implementation details

## Examples

- **[examples/neural_networks.txt](examples/neural_networks.txt)**: Well-formed atomic statements
- **[examples/bad_example.txt](examples/bad_example.txt)**: Anti-patterns and violations
- **[examples/expected_output.json](examples/expected_output.json)**: Sample output structure

## Testing

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# Specific test file
pytest tests/test_nodes.py -v
```

## Features

✅ **Atomic Node Creation** - Self-contained semantic units with validation  
✅ **Typed Relationships** - 6 relationship types with strict validation  
✅ **Atomicity Validation** - Pronoun detection, single-claim enforcement  
✅ **Semantic Similarity** - Deduplication and related_to edges  
✅ **Evidence Tracking** - Full provenance chain for all assertions  
✅ **Projection System** - Reversible lenses for cognitive navigation (7 perspectives)  
✅ **CLI Interface** - Ingest, validate, stats, projectnodes  
✅ **CLI Interface** - Ingest, validate, stats commands  
✅ **Python API** - Programmatic access to all features  
✅ **Fallback Mode** - Works with or without ML dependencies  

## Dependencies

### Core (Required)
- Python 3.9+
- pydantic>=2.0.0
- numpy>=1.24.0

### Optional (Recommended)
- sentence-transformers>=2.2.0 (for semantic similarity)
- scikit-learn>=1.3.0 (for ML utilities)

**Note**: System works with basic text similarity if sentence-transformers is unavailable. See [INSTALL.md](INSTALL.md) for details.

## Specification Compliance

This implementation is **fully compliant** with:

### INGESTION_SYSTEM_SPEC.v1.0 (Base Constraints)
- ✓ Relational truth layer (no hierarchies)
- ✓ Atomic nodes only
- ✓ Typed relationships only
- ✓ No ontological containment
- ✓ Evidence-backed assertions
- ✓ Append-only operations
- ✓ Reversibility guarantees
- ✓ No semantic freeloaders
- ✓ Connectivity enforcement

### INGESTION_CORRECTION_SPEC.v1.0 (Hardening Constraints)
- ✓ Meta-content elimination (docstrings, comments, headers)
- ✓ Single-claim atomicity enforcement
- ✓ Lexical trigger requirements for directed edges
- ✓ Non-null evidence spans mandatory
- ✓ Stopword-free canonical terms
- ✓ No implicit inference
- ✓ Strict compilation discipline

### INGESTION_SIMILARITY_MEASUREMENT_SPEC.v1.0 (Bounded Measurement)
- ✓ Top-K similarity measurement (K=10)
- ✓ No ingestion-time threshold cutoffs
- ✓ Measurement completeness within bounded horizon
- ✓ Linear growth (O(N×K))
- ✓ Projection-agnostic (thresholds applied at query time)
### PROJECTION_SYSTEM_SPEC.v1.0 (Cognitive Navigation)
- ✓ Truth layer immutability (no mutations)
- ✓ Reversible projections (parameter-reproducible)
- ✓ No new relationship inference
- ✓ Coherence threshold filtering (weighted edges only)
- ✓ Directed edges always included
- ✓ Seven perspective suite (varying threshold/depth)
- ✓ JSON-only structured output
- ✓ No clustering or derived ontology

**See [CORRECTION_SUMMARY.md](CORRECTION_SUMMARY.md) for hardening verification.**  
**See [MEASUREMENT_SUMMARY.md](MEASUREMENT_SUMMARY.md) for measurement architecture.**  
**See [PROJECTION_SUMMARY.md](PROJECTION_SUMMARY.md) for projection system details
**See [CORRECTION_SUMMARY.md](CORRECTION_SUMMARY.md) for hardening verification.**  
**See [MEASUREMENT_SUMMARY.md](MEASUREMENT_SUMMARY.md) for measurement architecture.**

## Contributing

Contributions welcome! Please:
1. Read [SPECIFICATION.md](SPECIFICATION.md) for design principles
2. Check [USAGE.md](USAGE.md) for usage patterns
3. Run tests before submitting PRs
4. Maintain specification compliance

## License

See [LICENSE](LICENSE) file.

## Support

- **Issues**: Check [INSTALL.md](INSTALL.md) for troubleshooting
- **Usage**: See [USAGE.md](USAGE.md) for comprehensive guide
- **Examples**: Explore [examples/](examples/) directory
- **Tests**: Review [tests/](tests/) for usage patterns

## Citation

```bibtex
@software{relational_knowledge_fabric_2026,
  title={Relational Knowledge Fabric Ingestion System},
  author={Taylor, Chris},
  year={2026},
  version={1.0.0},
  note={Implementation of INGESTION_SYSTEM_SPEC.v1.0}
}
```+ CORRECTION_SPEC v1.0  
**Status**: ✅ Production Ready - Hardened
## Acknowledgments

Built following the **INGESTION_SYSTEM_SPEC.v1.0** specification, which emphasizes:
- Relational truth over hierarchical structures
- Compilation over interpretation
- Evidence-backed assertions
- Reversibility guarantees

---

**Version**: 1.0.0  
**Status**: ✅ Production Ready  
**Last Updated**: March 4, 2026
