# Installation Guide

## Requirements

- Python 3.9 or higher
- pip package manager

## Quick Install

```bash
pip install -r requirements.txt
```

## Dependencies

### Core Dependencies
- **pydantic>=2.0.0**: Data validation and modeling
- **numpy>=1.24.0**: Numerical operations

### Optional Dependencies (for full functionality)

#### Semantic Similarity (Recommended)
For semantic similarity and deduplication:
```bash
pip install sentence-transformers>=2.2.0
```

**Note**: sentence-transformers requires PyTorch 2.1+. If you have PyTorch issues, the system will fall back to basic text similarity.

#### scikit-learn
For additional ML utilities:
```bash
pip install scikit-learn>=1.3.0
```

## Dependency Issues

### PyTorch Version Conflicts

If you encounter PyTorch version conflicts with sentence-transformers, you have two options:

**Option 1**: Install compatible PyTorch first
```bash
pip install torch>=2.1.0 --index-url https://download.pytorch.org/whl/cpu
pip install sentence-transformers>=2.2.0
```

**Option 2**: Use basic similarity fallback
The system will automatically fall back to basic text similarity if sentence-transformers is unavailable. This provides:
- Hash-based exact matching
- Token overlap similarity
- No semantic understanding (less accurate)

To use basic mode explicitly:
```bash
# Don't install sentence-transformers
pip install pydantic>=2.0.0 numpy>=1.24.0
```

### Conda Environment (Recommended)

For a clean install:
```bash
# Create environment
conda create -n knowledge-fabric python=3.9
conda activate knowledge-fabric

# Install PyTorch
conda install pytorch>=2.1.0 -c pytorch

# Install other dependencies
pip install -r requirements.txt
```

### Virtual Environment

```bash
# Create venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Verification

Test your installation:

```bash
# Test core functionality (no ML required)
python -c "from src.core import AtomicNode, Evidence; print('✅ Core OK')"

# Test full system (requires sentence-transformers)
python -c "from src.engine import IngestionEngine; print('✅ Full system OK')"
```

## Minimal Install (Core Only)

For environments with restricted dependencies:

```bash
pip install pydantic>=2.0.0 numpy>=1.24.0
```

This provides:
- ✅ Atomic node creation and validation
- ✅ Graph construction and management
- ✅ Edge type validation
- ✅ Basic text parsing
- ✅ Evidence tracking
- ⚠️ Limited deduplication (hash-based only)
- ⚠️ No semantic similarity edges

## Platform-Specific Notes

### Linux
No special requirements.

### macOS
No special requirements.

### Windows
- Git Bash or WSL recommended for running shell scripts
- PowerShell works for Python commands

## Development Install

For development with testing:
```bash
pip install -e ".[dev]"
```

This installs:
- pytest
- pytest-cov
- black (code formatting)
- ruff (linting)

## Troubleshooting

### Import Errors
```python
ModuleNotFoundError: No module named 'sentence_transformers'
```
**Solution**: Install sentence-transformers or use basic mode.

### PyTorch Errors
```
AttributeError: module 'torch' has no attribute 'compiler'
```
**Solution**: Upgrade PyTorch to 2.1+ or use basic mode.

### Pydantic Errors
```
ImportError: cannot import name 'BaseModel' from 'pydantic'
```
**Solution**: Upgrade pydantic to v2: `pip install -U pydantic>=2.0`

## Next Steps

After installation:
1. Read [USAGE.md](USAGE.md) for usage guide
2. Try `python demo.sh` for interactive demo
3. Check [examples/](examples/) for sample inputs
4. Run `pytest tests/` to verify everything works
