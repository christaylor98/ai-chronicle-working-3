# INGESTION_SYSTEM_SPEC.v1.0

This document describes the authoritative specification that this implementation follows.

## Core Principles

1. **Relational truth is primary**
   - The truth layer consists only of atomic nodes and typed relationships
   - No hierarchies, no ontological containment

2. **Ingestion is compilation, not interpretation**
   - Transform raw content into atomic units
   - No summarization, clustering, or abstraction
   - Preserve relational truth without projection distortion

3. **Atomic units must earn their keep**
   - Every node must justify existence through connectivity
   - Orphaned nodes are queued as candidates
   - No semantic freeloaders

4. **Constraint > Priority > Goal**
   - Hard limits are inviolable
   - Design decisions respect constraints first

5. **Map is a lens over truth**
   - Projections happen in query/visualization layers
   - Ingestion must not perform projection work

6. **Reversibility guaranteed**
   - Append-only operations
   - Full evidence chain for all additions
   - Merges/splits must be proposed, never executed

## Hard Constraints

These constraints MUST be enforced by the implementation:

1. Truth layer consists ONLY of atomic nodes and typed relationships
2. Documents are context nodes, NOT containers
3. All atomic nodes must be self-contained and minimally sufficient
4. Every node must connect to at least one other node or be queued as candidate
5. Every relationship must match an allowed type exactly
6. No implicit merging, clustering, summarizing, or abstraction
7. All nodes and edges must include evidence provenance

## Atomic Node Requirements

An atomic node must satisfy ALL of these tests:

1. **Self-contained**: Statement makes sense independently
2. **No external pronouns**: Does not rely on context for meaning
3. **Single claim**: Expresses exactly one semantic unit
4. **Non-redundant**: Not similar to existing node above threshold

Required fields:
- `node_id`: Unique identifier
- `statement`: The atomic semantic unit
- `canonical_terms[]`: Key terms for indexing
- `evidence[]`: Provenance chain
- `stability_hash`: Content-based deduplication hash

## Context Node Requirements

Context nodes represent source files as evidence carriers:

- Does NOT contain other nodes
- Provides evidence for `appears_in` relationships
- Allowed edges: `appears_in`, `authored_by`

## Relationship Types

### Weighted (Continuous 0.0-1.0)

**related_to**: Semantic similarity between atomic nodes

### Directed (Boolean)

- **derived_from**: Target provides justification/origin of source
- **refines**: Source narrows or specializes target
- **depends_on**: Source requires target to be valid
- **authored_by**: Context node linked to author entity
- **appears_in**: Atomic node evidenced within context node

## Edge Validation Rules

Every edge must satisfy:

1. Edge type matches allowed semantics
2. Direction is meaning-preserving
3. Edge has evidence pointer
4. Edge does not encode containment or hierarchy
5. Source and target node types are valid for edge type

## Output Format

Ingestion produces a **truth delta** only:

```
nodes_added[]      - New atomic and context nodes
edges_added[]      - New typed relationships
weights_added[]    - New weighted relationships
candidates[]       - Statements that failed admission
provenance[]       - Evidence chain for all additions
```

Prohibited in output:
- Summaries
- Clusters
- Hierarchies
- Projection artifacts
- Containment relationships

## No Semantic Freeloaders

Admission rule: Nodes or edges that do not increase relational clarity or connectivity must be placed in `candidates[]`.

## Success Criteria

The ingestion is successful if:

- Graph remains sparse, precise, and evidence-backed
- Each node is independently meaningful
- Each relationship is justifiable and inspectable
- No nodes bundle multiple claims
- No relationships imply containment or narrative flow

## Failure Indicators

The ingestion has failed if:

- Graph resembles document structure (hierarchical)
- Nodes contain multiple bundled claims
- Relationships imply containment or narrative flow
- Nodes exist without connectivity justification
- Evidence chains are missing or incomplete

## Phase Restrictions

During ingestion phase:

- **Allowed**: Truth delta output only
- **Prohibited**: Design, projection, clustering
- **Mode**: Compilation only, no interpretation

## Implementation Notes

This implementation (v1.0.0) provides:

1. **Core data models** ([src/core/](src/core/))
   - Pydantic models with validation
   - Hash-based deduplication
   - Evidence tracking

2. **Ingestion pipeline** ([src/ingestion/](src/ingestion/))
   - Text parsing and extraction
   - Atomicity validation
   - Relationship inference

3. **Utilities** ([src/utils/](src/utils/))
   - Semantic similarity (sentence transformers)
   - Provenance tracking

4. **Main engine** ([src/engine.py](src/engine.py))
   - Orchestrates complete pipeline
   - Enforces all constraints
   - Produces truth delta

5. **CLI interface** ([main.py](main.py))
   - Ingest, validate, stats commands
   - User-friendly error messages

All constraints from the specification are enforced at runtime through validation, type checking, and graph invariants.
