#!/bin/bash
# Quick demo of the relational knowledge fabric ingestion system

set -e

echo "=============================================="
echo "Relational Knowledge Fabric Ingestion Demo"
echo "=============================================="
echo ""

# Check if dependencies are installed
if ! python -c "import sentence_transformers" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    echo ""
fi

# Demo 1: Good example
echo "1. Ingesting good example (neural_networks.txt)..."
echo "   This file contains well-formed atomic statements."
echo ""
python main.py ingest examples/neural_networks.txt -o demo_good.json --author "Demo"
echo ""

# Show stats
echo "2. Analyzing the resulting graph..."
echo ""
python main.py stats demo_good.json
echo ""

# Validate
echo "3. Validating graph structure..."
echo ""
python main.py validate demo_good.json
echo ""

# Demo 2: Bad example
echo "4. Ingesting bad example (bad_example.txt)..."
echo "   This file contains statements that violate atomicity."
echo ""
python main.py ingest examples/bad_example.txt -o demo_bad.json --author "Demo"
echo ""

echo "5. Comparing results..."
echo ""
python main.py stats demo_bad.json
echo ""

echo "=============================================="
echo "Demo complete!"
echo ""
echo "Files created:"
echo "  - demo_good.json (well-formed atomic graph)"
echo "  - demo_bad.json (shows validation issues)"
echo ""
echo "Review the JSON files to see:"
echo "  - Atomic nodes extracted"
echo "  - Typed relationships inferred"
echo "  - Candidates that failed validation"
echo "  - Complete provenance tracking"
echo ""
echo "See USAGE.md for detailed guide."
echo "=============================================="
