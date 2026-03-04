# INGESTION_SYSTEM_SPEC.v1.0 + CORRECTION_SPEC.v1.0 + MEASUREMENT_SPEC.v1.0

This document describes the authoritative specification that this implementation follows, including hardening corrections and similarity measurement discipline.

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

### Base Constraints (v1.0)
1. Truth layer consists ONLY of atomic nodes and typed relationships
2. Documents are context nodes, NOT containers
3. All atomic nodes must be self-contained and minimally sufficient
4. Every node must connect to at least one other node or be queued as candidate
5. Every relationship must match an allowed type exactly
6. No implicit merging, clustering, summarizing, or abstraction
7. All nodes and edges must include evidence provenance

### Hardening Constraints (CORRECTION_SPEC v1.0)

#### Meta-Content Elimination
8. Lines that are comments, docstrings, markdown headers, or instructional scaffolding MUST NOT produce atomic nodes
9. Text inside triple-quoted blocks MUST be discarded unless explicitly marked as domain knowledge
10. Lines beginning with comment markers (#, //, etc.) MUST be discarded before atomic extraction

#### Atomic Purity Enforcement
11. Each atomic node must contain exactly one declarative domain claim
12. If a sentence contains multiple claims joined by conjunction, it MUST be split or placed in candidates[]

#### Directed Edge Discipline
13. Directed edges (derived_from, refines, depends_on) MUST only be created when explicit lexical triggers are present in the source span
14. Allowed lexical triggers for depends_on: 'depends on', 'requires', 'relies on'
15. Allowed lexical triggers for derived_from: 'derived from', 'follows from', 'based on'
16. Allowed lexical triggers for refines: 'more specifically', 'in particular', 'more precisely'
17. If no explicit lexical trigger exists, directed edge MUST NOT be created

#### Evidence Integrity
18. Every edge MUST include a non-null evidence span referencing the original context
19. Edges with null span MUST NOT be emitted

#### Canonical Term Hygiene
20. Stopwords and articles (e.g., 'the', 'a', 'an', 'is', 'are', 'and', 'or') MUST NOT appear in canonical_terms

### Relational Enrichment Constraints (ENRICHMENT_SPEC v1.0)

#### Purpose
Add disciplined `related_to` edge generation to increase relational density without introducing ontological distortion.

#### Hard Constraints for related_to Edges

21. **Semantic similarity only**: `related_to` edges represent weighted semantic similarity ONLY. They MUST NOT imply causation, derivation, refinement, or dependency.

22. **No directed inference**: No directed edge (derived_from, refines, depends_on) may be inferred from a `related_to` edge.

23. **Fixed threshold**: Similarity threshold is FIXED at 0.65 and MUST be explicit. Threshold tuning MUST NOT be based on readability or visual density goals.

24. **Weight requirement**: All `related_to` edges MUST include a numeric weight between 0.0 and 1.0.

25. **Threshold enforcement**: `related_to` edges below threshold (< 0.65) MUST NOT be emitted.

26. **Symmetry**: `related_to` edges MUST be symmetric. Inverse edges MUST NOT be duplicated (e.g., if A→B exists, B→A should not).

27. **No self-links**: Nodes MUST NOT have `related_to` edges to themselves.

28. **No clustering**: No clustering, grouping, or containment may be introduced during enrichment. Clusters may only exist in projection layers.

29. **Method provenance**: Each `related_to` edge MUST include metadata identifying the similarity method used (e.g., "embedding_cosine", "basic_bow_cosine").

30. **Sparsity preservation**: Edges MUST NOT be pruned for aesthetic sparsity. Let natural threshold determine density.

#### Similarity Method

- Fixed threshold: 0.65
- Symmetric (no duplicate inverses)
- Includes similarity method metadata
- Does NOT imply causation or dependency
- **Method**: Embedding cosine similarity (sentence transformers) or basic bag-of-words cosine (fallback)
- **Threshold**: Fixed at 0.65
- **Pairwise computation**: All atomic nodes compared pairwise
- **Symmetry enforcement**: Only emit one edge per pair (i < j)
- **Self-link prevention**: Never compare node to itself

#### Failure Conditions

Enrichment has failed if:
- `related_to` edges imply directionality
- `related_to` edges are used to justify directed edges
- Similarity threshold dynamically adapts to density
- Graph becomes fully connected
- Clusters are stored as ontology in truth layer

#### Success Criteria

Enrichment is successful if:
- Semantically adjacent claims exhibit measurable `related_to` weights
- Graph remains sparse but connected
- Directed edges remain lexically grounded only
- Projection layer can form clusters without altering truth layer

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

**related_to**: Semantic similarity measurement between atomic nodes
- **Top-K bounded** (K=10): Each node retains 10 most similar neighbors
- **NO global threshold**: All top-K measurements stored
- **Symmetric**: No duplicate inverse edges
- **Method provenance**: Metadata includes similarity method
- **Does NOT imply**: causation, dependency, or refinement
- **Threshold filtering**: Happens in projection layer, not ingestion
- **Linear growth**: Max edges = N × K (bounded)

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
