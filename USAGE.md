# Relational Knowledge Fabric - Usage Guide

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or with development dependencies
pip install -e ".[dev]"
```

### Basic Usage

1. **Ingest a file**:
```bash
python main.py ingest examples/neural_networks.txt
```

This will:
- Parse the file into atomic semantic units
- Validate atomicity of each statement
- Create a relational knowledge graph
- Output a JSON file with the truth delta

2. **Specify output location**:
```bash
python main.py ingest input.txt -o output.json
```

3. **Add metadata**:
```bash
python main.py ingest input.txt \
  --author "John Doe" \
  --description "Machine learning concepts"
```

4. **Adjust similarity threshold**:
```bash
python main.py ingest input.txt -t 0.90  # Stricter deduplication
```

5. **Use permissive mode** (less strict atomicity validation):
```bash
python main.py ingest input.txt --permissive
```

### Validation

Check if a graph file is valid:

```bash
python main.py validate output.json
```

### Statistics

Analyze a knowledge graph:

```bash
python main.py stats output.json
```

This shows:
- Node counts (atomic, context)
- Edge counts and distribution
- Quality metrics (connectivity, candidate ratio)
- Average semantic similarity

## Understanding the Output

### Structure

The output JSON contains:

```json
{
  "nodes_added": [...],      // Atomic and context nodes
  "edges_added": [...],      // Directed relationships
  "weights_added": [...],    // Semantic similarity edges
  "candidates": [...],       // Statements that failed validation
  "provenance": [...]        // Evidence chain for all additions
}
```

### Atomic Nodes

Each atomic node represents a self-contained semantic unit:

```json
{
  "node_id": "atomic_abc123",
  "statement": "Neural networks are computational models",
  "canonical_terms": ["neural", "networks", "computational"],
  "evidence": [{"source": "context_xyz", "span": [0, 42]}],
  "stability_hash": "abc123",
  "created_at": "2026-03-04T12:00:00",
  "node_type": "atomic"
}
```

### Context Nodes

Context nodes represent source files (not containers):

```json
{
  "node_id": "context_xyz789",
  "source_file": "input.txt",
  "content_hash": "xyz789",
  "metadata": {"author": "John Doe"},
  "created_at": "2026-03-04T12:00:00",
  "node_type": "context"
}
```

### Edges

Typed relationships between nodes:

```json
{
  "source": "atomic_1",
  "target": "atomic_2",
  "type": "derived_from",
  "evidence": [...]
}
```

Edge types:
- **related_to** (weighted): Semantic similarity
- **derived_from**: Target justifies source
- **refines**: Source specializes target
- **depends_on**: Source requires target
- **appears_in**: Atomic node appears in context
- **authored_by**: Context authored by entity

### Candidates

Statements that failed validation:

```json
{
  "statement": "This enables better performance",
  "reason": "Statement starts with dependency pronoun 'this'",
  "evidence": [...],
  "proposed_node_id": null
}
```

Review candidates to improve your input quality.

## Best Practices

### Writing Atomic Content

**Good** ✓:
```
Neural networks are computational models inspired by biological systems.
Backpropagation computes gradients for neural network training.
Transformers use self-attention mechanisms for sequence processing.
```

**Bad** ✗:
```
It works by processing inputs through layers.
This enables pattern recognition, and it's very important.
They are useful for many tasks.
```

### Atomicity Rules

1. **Self-contained**: Statement should make sense without external context
2. **No pronouns at start**: Don't begin with "this", "that", "it", etc.
3. **Single claim**: One semantic unit per statement
4. **Meaningful**: Must have substantive content

### Structuring Input

- Use one statement per line or paragraph
- Bullet points work well
- Numbered lists are extracted automatically
- Avoid narrative flow with pronouns

### Similarity Threshold

- **0.85** (default): Balanced - removes near-duplicates
- **0.90**: Stricter - only removes very similar statements
- **0.80**: More lenient - may merge related but distinct concepts

## Advanced Usage

### Python API

```python
from src.engine import IngestionEngine

# Initialize
engine = IngestionEngine(similarity_threshold=0.85)

# Ingest
truth_delta = engine.ingest_file(
    "input.txt",
    author="John Doe",
    metadata={"domain": "machine_learning"}
)

# Export
engine.export_truth_delta("output.json")

# Get statistics
stats = engine.get_statistics()
print(f"Created {stats['atomic_nodes']} atomic nodes")
```

### Custom Validation

```python
from src.ingestion import AtomicityValidator

validator = AtomicityValidator(strict=True)
is_valid, violations = validator.validate("Your statement here")

if not is_valid:
    for v in violations:
        print(f"{v.rule}: {v.description}")
        print(f"  Suggestion: {v.suggestion}")
```

### Similarity Analysis

```python
from src.utils import SimilarityEngine

sim_engine = SimilarityEngine()
similarity = sim_engine.compute_similarity(
    "Neural networks learn patterns",
    "Deep learning models recognize patterns"
)
print(f"Similarity: {similarity:.3f}")
```

## Troubleshooting

### High Candidate Ratio

If many statements become candidates:
1. Review atomicity guidelines
2. Use `--permissive` mode for exploratory ingestion
3. Preprocess text to remove narrative elements

### Low Connectivity

If many orphaned nodes:
1. Ensure content has thematic coherence
2. Lower similarity threshold slightly
3. Add transitional statements that link concepts

### Slow Processing

For large files:
1. Split into smaller thematic chunks
2. The similarity engine caches embeddings
3. Consider using GPU for sentence transformers

## Testing

Run the test suite:

```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# Specific test file
pytest tests/test_nodes.py -v
```

## Architecture

```
Input File
    ↓
TextParser → Extract candidate units
    ↓
AtomicityValidator → Validate self-containment
    ↓
AtomicNode.create() → Generate nodes with evidence
    ↓
RelationshipBuilder → Infer typed relationships
    ↓
KnowledgeGraph → Validate connectivity
    ↓
Truth Delta (JSON output)
```

## Specification Compliance

This implementation adheres to **INGESTION_SYSTEM_SPEC.v1.0**:

- ✓ Relational truth layer (no hierarchies)
- ✓ Atomic nodes only
- ✓ Typed relationships only
- ✓ No ontological containment
- ✓ Evidence-backed assertions
- ✓ Append-only operations
- ✓ Reversibility guarantees
- ✓ No semantic freeloaders
- ✓ Connectivity enforcement

## Support

For issues, improvements, or questions:
1. Check examples/ directory for patterns
2. Review test cases for usage examples
3. Consult the specification document
