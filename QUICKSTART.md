# Quick Start Guide

## 5-Minute Quickstart

### 1. Verify Installation

```bash
# Test core functionality (no ML dependencies needed)
python -c "from src.core import AtomicNode, Evidence; print('✅ Core OK')"
```

### 2. Run Your First Ingestion

```bash
# Create test input
cat > test.txt << 'EOF'
Neural networks are computational models.
Deep learning uses multiple layers.
Backpropagation trains neural networks.
Convolutional networks process images.
Transformers use attention mechanisms.
EOF

# Ingest the file
python main.py ingest test.txt -o output.json

# You should see:
# Ingestion complete!
#   Atomic nodes: 5
#   Context nodes: 1
#   ...
```

### 3. Validate the Output

```bash
python main.py validate output.json

# You should see:
# ✓ Graph structure valid
# ✓ No validation warnings
```

### 4. Analyze the Graph

```bash
python main.py stats output.json

# You should see detailed statistics:
# - Node counts
# - Edge distribution
# - Quality metrics
```

### 5. Explore the Output

```bash
# View the JSON output
python -m json.tool output.json | less

# Or open in your favorite JSON viewer
```

## What You'll See

The system creates:

1. **Atomic Nodes** - One per well-formed statement:
```json
{
  "node_id": "atomic_4f2a112319801270",
  "statement": "Neural networks are computational models",
  "canonical_terms": ["Neural", "networks", "computational"],
  "evidence": [{"source": "context_...", "span": [0, 40]}],
  "stability_hash": "4f2a112319801270"
}
```

2. **Context Node** - Represents the source file:
```json
{
  "node_id": "context_5dded314b0e7cb93",
  "source_file": "test.txt",
  "content_hash": "5dded314b0e7cb93"
}
```

3. **Edges** - Link nodes to their context:
```json
{
  "source": "atomic_4f2a112319801270",
  "target": "context_5dded314b0e7cb93",
  "type": "appears_in",
  "evidence": [...]
}
```

## Common Commands

### Ingest with Metadata
```bash
python main.py ingest input.txt \
  --author "John Doe" \
  --description "ML concepts" \
  --output graph.json
```

### Adjust Similarity Threshold
```bash
# Stricter deduplication (higher threshold)
python main.py ingest input.txt -t 0.90

# More lenient (lower threshold)
python main.py ingest input.txt -t 0.80
```

### Permissive Mode
```bash
# Less strict atomicity validation
python main.py ingest input.txt --permissive
```

## Troubleshooting

### "Warning: sentence-transformers not available"
This is OK! The system falls back to basic text similarity.
- ✅ Core functionality works
- ⚠️ Semantic similarity is less accurate
- To fix: `pip install sentence-transformers>=2.2.0`

### "AttributeError: module 'torch' has no attribute 'compiler'"
PyTorch version is too old.
- ✅ System still works in fallback mode
- To fix: `pip install torch>=2.1.0`

### High Candidate Ratio
Many statements failed validation.
- Review atomicity guidelines in USAGE.md
- Try `--permissive` mode
- Check examples/bad_example.txt for anti-patterns

## Next Steps

1. **Read the guides**:
   - [USAGE.md](USAGE.md) - Comprehensive usage guide
   - [SPECIFICATION.md](SPECIFICATION.md) - Technical specification
   - [INSTALL.md](INSTALL.md) - Dependency troubleshooting

2. **Explore examples**:
   - [examples/neural_networks.txt](examples/neural_networks.txt) - Good patterns
   - [examples/bad_example.txt](examples/bad_example.txt) - Anti-patterns

3. **Try your own content**:
   - Start with well-formed atomic statements
   - One claim per statement
   - Avoid pronouns without clear referents
   - Keep statements self-contained

4. **Experiment with settings**:
   - Similarity thresholds
   - Strict vs permissive validation
   - Different content types

## Python API Example

```python
from src.engine import IngestionEngine

# Create engine
engine = IngestionEngine(
    similarity_threshold=0.85,
    strict_validation=True
)

# Ingest file
truth_delta = engine.ingest_file(
    "input.txt",
    author="John Doe",
    metadata={"domain": "AI"}
)

# Export
engine.export_truth_delta("output.json")

# Get stats
stats = engine.get_statistics()
print(f"Created {stats['atomic_nodes']} atomic nodes")
```

## Success Criteria

Your ingestion is successful if:
- ✅ Candidates ratio < 10%
- ✅ All atomic nodes have connectivity
- ✅ Edges have proper types
- ✅ Evidence trails are complete
- ✅ Statements are self-contained

## Getting Help

- **Installation issues**: See [INSTALL.md](INSTALL.md)
- **Usage questions**: See [USAGE.md](USAGE.md)
- **Understanding output**: Check [examples/expected_output.json](examples/expected_output.json)
- **API reference**: See docstrings in source files

---

Happy ingesting! 🚀
