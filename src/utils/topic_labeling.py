"""
Batched LLM topic labeling for atomic nodes.

Per BATCH_LLM_TOPIC_LABELLING_SPEC.v1.0:
- One ai_factory API call per ingestion batch
- Labels all atomic nodes in a single request
- Specific labels (e.g., 'ancient-egypt' not 'history')
- Works for arbitrary unknown domains
- Graceful fallback to ['general'] on failure
- Zero per-node API overhead

Per BATCH_LABEL_CHUNKING_SPEC.v1.0:
- Splits large batches into chunks of 50 nodes (configurable)
- One ai_factory API call per chunk
- Node numbering resets to 1 for each chunk
- Failed chunks fall back to 'general' without crashing
- Total API calls = ceil(node_count / chunk_size)
"""

import re
import math
from typing import List, Dict
from ai_factory import run
from ai_factory.config import Config


def assign_topic_labels_batch(
    statements: List[str],
    model: str = "gpt-5-mini",
    provider: str = "copilot_cli",
    chunk_size: int = 50
) -> List[List[str]]:
    """
    Assign topic labels to all atomic nodes via chunked batched LLM calls.
    
    Per BATCH_LABEL_CHUNKING_SPEC.v1.0:
    - Splits statements into chunks of chunk_size (default: 50)
    - Makes ONE ai_factory run() call per chunk
    - Node numbering resets to 1 for each chunk
    - Returns 2-3 specific labels per node
    - Labels are lowercase hyphenated strings
    - Failed chunks fall back to ['general'] without crashing
    
    Args:
        statements: List of N atomic statement texts
        model: LLM model to use (default: gpt-5-mini)
        provider: LLM provider (default: copilot_cli)
        chunk_size: Maximum nodes per API call (default: 50)
    
    Returns:
        List of label lists, one per node (e.g., [['ancient-egypt', 'nile'], ...])
    
    Example:
        >>> statements = [
        ...     "The pyramids were built during Egypt's Old Kingdom",
        ...     "Quantum entanglement links particle states across distances"
        ... ]
        >>> labels = assign_topic_labels_batch(statements)
        >>> labels
        [['ancient-egypt', 'pyramids'], ['quantum-physics', 'entanglement']]
    """
    if not statements:
        return []
    
    # Handle single node case (no chunking needed)
    if len(statements) == 1:
        return _label_single_node(statements[0], model, provider)
    
    # Calculate number of chunks needed
    num_chunks = math.ceil(len(statements) / chunk_size)
    
    if num_chunks == 1:
        # Small batch - use original single-batch implementation
        return _label_batch_chunk(statements, model, provider)
    
    # Large batch - split into chunks
    print(f"Splitting {len(statements)} nodes into {num_chunks} chunks of {chunk_size}...")
    
    all_labels = []
    
    for chunk_idx in range(num_chunks):
        start_idx = chunk_idx * chunk_size
        end_idx = min(start_idx + chunk_size, len(statements))
        chunk = statements[start_idx:end_idx]
        
        print(f"  Processing chunk {chunk_idx + 1}/{num_chunks} ({len(chunk)} nodes)...", end=" ")
        
        try:
            chunk_labels = _label_batch_chunk(chunk, model, provider)
            all_labels.extend(chunk_labels)
            print("✓")
        except Exception as e:
            # Chunk failed - assign 'general' to all nodes in this chunk
            print(f"✗ (fallback to 'general')")
            print(f"    Warning: Chunk {chunk_idx + 1} failed ({e})")
            all_labels.extend([['general'] for _ in chunk])
    
    return all_labels


def _label_batch_chunk(
    statements: List[str],
    model: str,
    provider: str
) -> List[List[str]]:
    """
    Label a single chunk of statements with one AI call.
    
    Node numbering always starts at 1 for each chunk.
    
    Args:
        statements: List of statements (1 to chunk_size)
        model: LLM model to use
        provider: LLM provider
    
    Returns:
        List of label lists (one per statement)
    """
    # Step 1: Build numbered statement list (1-indexed, resets per chunk)
    numbered_statements = "\n".join(
        f"{i+1}. {stmt}" for i, stmt in enumerate(statements)
    )
    
    # Step 2: Build single batch prompt
    prompt = f"""For each numbered statement below, return 2-3 specific topic labels.
Format: one line per statement as: N: label1, label2, label3
Rules:
- Be specific: 'ancient-egypt' not 'history', 'quantum-physics' not 'science'
- Use lowercase hyphenated strings
- 2-3 labels per statement maximum
- Return only the numbered label lines, nothing else

Statements:
{numbered_statements}"""
    
    # Step 3: Make single batched API call for this chunk
    config = Config(
        provider="ollama",
        model="qwen2.5:14b",
        ledger_enabled=False,
        base_url="http://localhost:11434"
    )
    result = run(prompt=prompt, config=config)
    response = result.output
    
    # Parse response into per-node labels
    labels_list = _parse_batch_response(response, len(statements))
    return labels_list


def _label_single_node(
    statement: str,
    model: str,
    provider: str
) -> List[List[str]]:
    """
    Label a single node (simplified prompt for single case).
    
    Args:
        statement: Single atomic statement
        model: LLM model to use
        provider: LLM provider
    
    Returns:
        List containing one label list
    """
    prompt = f"""Return 2-3 specific topic labels for this statement.
Format: label1, label2, label3
Rules:
- Be specific: 'ancient-egypt' not 'history', 'quantum-physics' not 'science'
- Use lowercase hyphenated strings
- Return only the comma-separated labels, nothing else

Statement: {statement}"""
    
    try:
        config = Config(
            provider="ollama",
            model="qwen2.5:14b",
            ledger_enabled=False,
            base_url="http://localhost:11434"
        )
        result = run(prompt=prompt, config=config)
        response = result.output
        
        # Parse comma-separated labels
        labels = _parse_comma_separated(response)
        return [labels]
    
    except Exception as e:
        print(f"Warning: Topic labeling failed ({e}), assigning 'general' label")
        return [['general']]


def _parse_batch_response(response: str, expected_count: int) -> List[List[str]]:
    """
    Parse batched LLM response into per-node label lists.
    
    Expected format:
        1: label1, label2, label3
        2: label1, label2
        3: label1, label2, label3
    
    Args:
        response: Raw LLM response text
        expected_count: Number of statements to parse labels for
    
    Returns:
        List of label lists (length = expected_count)
    """
    # Pattern: "N: label1, label2, label3"
    line_pattern = re.compile(r'^(\d+):\s*(.+)$', re.MULTILINE)
    
    # Build map from statement index to labels
    labels_map: Dict[int, List[str]] = {}
    
    for match in line_pattern.finditer(response):
        idx = int(match.group(1)) - 1  # Convert to 0-based
        labels_str = match.group(2).strip()
        
        # Parse comma-separated labels
        labels = _parse_comma_separated(labels_str)
        labels_map[idx] = labels
    
    # Build result list with fallback for missing/unparseable lines
    labels_list = []
    for i in range(expected_count):
        if i in labels_map:
            labels_list.append(labels_map[i])
        else:
            # Missing or unparseable line - fallback to ['general']
            labels_list.append(['general'])
    
    return labels_list


def _parse_comma_separated(labels_str: str) -> List[str]:
    """
    Parse comma-separated label string into list.
    
    Args:
        labels_str: "label1, label2, label3"
    
    Returns:
        List of cleaned labels (lowercase, stripped)
    """
    labels = []
    
    for label in labels_str.split(','):
        label = label.strip().lower()
        
        # Remove any quotes, periods, or other punctuation
        label = re.sub(r'["\'.;:!?]', '', label)
        
        # Replace spaces with hyphens
        label = re.sub(r'\s+', '-', label)
        
        if label and len(label) > 1:  # Minimum length
            labels.append(label)
    
    # Ensure at least one label
    if not labels:
        labels = ['general']
    
    # Limit to 3 labels maximum
    return labels[:3]
