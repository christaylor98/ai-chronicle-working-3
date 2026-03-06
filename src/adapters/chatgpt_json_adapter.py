"""
ChatGPT JSON Ingestion Adapter

Parses ChatGPT conversation export JSON files and feeds extracted assistant
message content into the existing IngestionEngine as discrete text chunks,
preserving timestamps as node metadata for future temporal projection.

Spec: CHATGPT_JSON_INGESTION_ADAPTER_SPEC.v1.0
"""

import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.engine import IngestionEngine


@dataclass
class ChatGPTChunk:
    """Represents an extracted assistant message from a ChatGPT conversation."""
    text: str
    timestamp: str  # ISO 8601
    conversation_id: str
    message_id: str
    conversation_title: Optional[str] = None


class ChatGPTJsonAdapter:
    """
    Adapter for ingesting ChatGPT JSON export files into the knowledge graph.
    
    Only extracts assistant messages, preserves timestamps, and handles
    malformed data gracefully. Does not modify IngestionEngine.
    """
    
    def __init__(self):
        """Initialize the adapter."""
        pass
    
    def parse_conversation(self, file_path: str) -> List[ChatGPTChunk]:
        """
        Parse a ChatGPT conversation JSON file and extract assistant messages.
        
        Args:
            file_path: Path to the ChatGPT JSON export file
            
        Returns:
            List of ChatGPTChunk objects containing assistant message text and metadata
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            json.JSONDecodeError: If the file is not valid JSON
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle both single conversation object and array of conversations
        if isinstance(data, dict):
            conversations = [data]
        elif isinstance(data, list):
            conversations = data
        else:
            raise ValueError(f"Expected dict or list, got {type(data)}")
        
        chunks = []
        
        for conv in conversations:
            conversation_id = conv.get('id') or conv.get('conversation_id', 'unknown')
            conversation_title = conv.get('title')
            mapping = conv.get('mapping', {})
            
            if not mapping:
                continue
            
            # Walk the message tree via children links from root
            # Find root node(s) - nodes with parent == null
            root_nodes = [node_id for node_id, node_data in mapping.items() 
                         if node_data.get('parent') is None]
            
            # Traverse tree breadth-first from each root
            visited = set()
            queue = root_nodes[:]
            
            while queue:
                node_id = queue.pop(0)
                if node_id in visited:
                    continue
                visited.add(node_id)
                
                node_data = mapping.get(node_id)
                if not node_data:
                    continue
                
                # Extract message if present
                message = node_data.get('message')
                if message and isinstance(message, dict):
                    # Only process assistant messages
                    author = message.get('author', {})
                    if not isinstance(author, dict):
                        continue
                    
                    role = author.get('role')
                    if role != 'assistant':
                        # Skip user and system messages
                        pass
                    else:
                        # Extract content
                        content = message.get('content', {})
                        if isinstance(content, dict):
                            parts = content.get('parts', [])
                            if isinstance(parts, list) and parts:
                                # Join all parts into single text
                                text_parts = [str(p) for p in parts if p]
                                text = '\n'.join(text_parts).strip()
                                
                                if text:  # Only add non-empty messages
                                    # Extract and convert timestamp
                                    create_time = message.get('create_time')
                                    if create_time:
                                        try:
                                            if isinstance(create_time, (int, float)):
                                                timestamp = datetime.fromtimestamp(create_time).isoformat()
                                            else:
                                                timestamp = str(create_time)
                                        except (ValueError, OSError):
                                            timestamp = datetime.now().isoformat()
                                    else:
                                        timestamp = datetime.now().isoformat()
                                    
                                    message_id = message.get('id', node_id)
                                    
                                    chunks.append(ChatGPTChunk(
                                        text=text,
                                        timestamp=timestamp,
                                        conversation_id=conversation_id,
                                        message_id=message_id,
                                        conversation_title=conversation_title
                                    ))
                
                # Add children to queue
                children = node_data.get('children', [])
                if isinstance(children, list):
                    queue.extend(children)
        
        return chunks
    
    def ingest_file(self, file_path: str, engine: IngestionEngine, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Ingest a single ChatGPT JSON file into the knowledge graph.
        
        Args:
            file_path: Path to the ChatGPT JSON export file
            engine: Initialized IngestionEngine instance
            output_path: Optional output path for checkpoint/resume functionality
            
        Returns:
            Merged TruthDelta from all ingested chunks
        """
        print(f"\nParsing ChatGPT conversation file: {file_path}")
        chunks = self.parse_conversation(file_path)
        
        if not chunks:
            print(f"  No assistant messages found in {file_path}")
            return {
                'nodes_added': [],
                'edges_added': [],
                'weights_added': []
            }
        
        print(f"  Found {len(chunks)} assistant messages\n")
        
        # Checkpoint file path
        checkpoint_path = None
        completed_batches = set()
        
        if output_path:
            checkpoint_path = output_path + '.checkpoint.json'
            
            # Try to load existing checkpoint
            if os.path.exists(checkpoint_path):
                print(f"📂 Found checkpoint file: {checkpoint_path}")
                try:
                    with open(checkpoint_path, 'r', encoding='utf-8') as f:
                        checkpoint = json.load(f)
                    
                    completed_batches = set(checkpoint.get('completed_batches', []))
                    
                    print(f"✓ Loaded checkpoint: {len(completed_batches)} batches already completed")
                    print(f"  Resuming from batch {len(completed_batches) + 1}...\n")
                    
                    # Start with accumulated data from checkpoint
                    merged_delta = {
                        'nodes_added': checkpoint.get('nodes_added', []),
                        'edges_added': checkpoint.get('edges_added', []),
                        'weights_added': checkpoint.get('weights_added', [])
                    }
                except Exception as e:
                    print(f"⚠ Warning: Could not load checkpoint: {e}")
                    print(f"  Starting fresh...\n")
                    merged_delta = {
                        'nodes_added': [],
                        'edges_added': [],
                        'weights_added': []
                    }
            else:
                print(f"Starting fresh ingestion (no checkpoint found)\n")
                merged_delta = {
                    'nodes_added': [],
                    'edges_added': [],
                    'weights_added': []
                }
        else:
            # No checkpoint support when output_path not provided
            merged_delta = {
                'nodes_added': [],
                'edges_added': [],
                'weights_added': []
            }
        
        # Dynamic batching: accumulate messages until we have ~50 nodes
        TARGET_NODES_PER_BATCH = 50
        
        print(f"Smart batching: accumulating messages until ~{TARGET_NODES_PER_BATCH} nodes per batch")
        print(f"(Maximizes LLM efficiency regardless of message size variation)\n")
        
        # First pass: quick extraction to count nodes per message
        print("Phase 1: Analyzing message sizes...")
        from src.ingestion import TextParser, AtomicityValidator
        parser = TextParser()
        validator = AtomicityValidator(strict=True)
        
        message_node_counts = []
        for i, chunk in enumerate(chunks):
            # Quick extract and validate to count atomic nodes
            extracted_units = parser.parse(chunk.text)
            
            # Count only valid atomic units
            valid_count = 0
            for unit in extracted_units:
                is_valid, _ = validator.validate(unit.text)
                if is_valid:
                    valid_count += 1
            
            message_node_counts.append(valid_count)
            
            if (i + 1) % 50 == 0:
                print(f"  Analyzed {i + 1}/{len(chunks)} messages...")
        
        print(f"✓ Analysis complete: {len(chunks)} messages → ~{sum(message_node_counts)} total nodes\n")
        
        # Phase 2: Create batches that reach ~50 nodes each
        print("Phase 2: Creating optimal batches...")
        batches = []
        current_batch = []
        current_node_count = 0
        
        for i, (chunk, node_count) in enumerate(zip(chunks, message_node_counts)):
            # Add message to current batch
            current_batch.append((i, chunk, node_count))
            current_node_count += node_count
            
            # If we've reached target, finalize this batch
            if current_node_count >= TARGET_NODES_PER_BATCH:
                batches.append((current_batch, current_node_count))
                current_batch = []
                current_node_count = 0
        
        # Add any remaining messages as final batch
        if current_batch:
            batches.append((current_batch, current_node_count))
        
        print(f"✓ Created {len(batches)} optimal batches")
        for batch_idx, (batch_msgs, node_count) in enumerate(batches):
            msg_range = f"{batch_msgs[0][0]+1}-{batch_msgs[-1][0]+1}"
            print(f"  Batch {batch_idx+1}: Messages {msg_range} → ~{node_count} nodes")
        print()
        
        # Phase 3: Process each batch
        print("Phase 3: Processing batches with topic labeling...")
        for batch_idx, (batch_messages, expected_nodes) in enumerate(batches):
            # Skip already-completed batches (resume logic)
            if batch_idx in completed_batches:
                print(f"\n{'='*60}")
                print(f"BATCH {batch_idx + 1}/{len(batches)}: SKIPPING (already completed)")
                print(f"{'='*60}")
                continue
            
            print(f"\n{'='*60}")
            print(f"BATCH {batch_idx + 1}/{len(batches)}: {len(batch_messages)} messages → ~{expected_nodes} nodes")
            print(f"{'='*60}")
            
            # Combine all messages in this batch
            batch_text_parts = []
            first_chunk = batch_messages[0][1]
            
            for msg_idx, chunk, node_count in batch_messages:
                print(f"  [{msg_idx+1}/{len(chunks)}] {chunk.conversation_title or 'Untitled'[:30]} | {chunk.timestamp[:19]} | ~{node_count} nodes")
                
                batch_text_parts.append(f"\n--- Message {msg_idx+1} ---\n")
                batch_text_parts.append(chunk.text)
                batch_text_parts.append("\n")
            
            # Write batch to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as tmp_file:
                tmp_file.write(''.join(batch_text_parts))
                tmp_path = tmp_file.name
            
            try:
                print(f"\n  → Processing batch through full pipeline...")
                
                # Prepare metadata from first message
                metadata = {
                    'timestamp': first_chunk.timestamp,
                    'conversation_id': first_chunk.conversation_id,
                    'message_id': first_chunk.message_id,
                    'source_type': 'chatgpt_conversation_batch',
                    'batch_size': len(batch_messages),
                    'expected_nodes': expected_nodes
                }
                if first_chunk.conversation_title:
                    metadata['conversation_title'] = first_chunk.conversation_title
                
                # Ingest batch (extraction + topic labeling + relationships)
                truth_delta = engine.ingest_file(tmp_path, metadata=metadata)
                
                # Merge results
                merged_delta['nodes_added'].extend(truth_delta['nodes_added'])
                merged_delta['edges_added'].extend(truth_delta['edges_added'])
                merged_delta['weights_added'].extend(truth_delta['weights_added'])
                
                print(f"\n  ✓ Batch complete: +{len(truth_delta['nodes_added'])} nodes, +{len(truth_delta['edges_added'])} edges")
                print(f"  ✓ Running total: {len(merged_delta['nodes_added'])} nodes, {len(merged_delta['edges_added'])} edges")
                
                # Mark batch as completed
                completed_batches.add(batch_idx)
                
                # Write checkpoint and output file after every batch
                if output_path and checkpoint_path:
                    # Write checkpoint
                    checkpoint_data = {
                        'completed_batches': sorted(list(completed_batches)),
                        'nodes_added': merged_delta['nodes_added'],
                        'edges_added': merged_delta['edges_added'],
                        'weights_added': merged_delta['weights_added'],
                        'total_nodes': len(merged_delta['nodes_added']),
                        'total_edges': len(merged_delta['edges_added'])
                    }
                    
                    with open(checkpoint_path, 'w', encoding='utf-8') as f:
                        json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
                    
                    # Write incremental output file (valid after every batch)
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(merged_delta, f, indent=2, ensure_ascii=False)
                    
                    print(f"  💾 Checkpoint saved: batch {batch_idx + 1}/{len(batches)} complete")
                
            finally:
                os.unlink(tmp_path)
        
        print(f"\n{'='*60}")
        print(f"✓ INGESTION COMPLETE")
        print(f"{'='*60}")
        print(f"  Total messages processed: {len(chunks)}")
        print(f"  Batches executed: {len(batches)}")
        print(f"  Nodes added: {len(merged_delta['nodes_added'])}")
        print(f"  Edges added: {len(merged_delta['edges_added'])}")
        print(f"  Weights added: {len(merged_delta['weights_added'])}")
        print(f"{'='*60}\n")
        
        # Delete checkpoint file on clean completion
        if output_path and checkpoint_path and os.path.exists(checkpoint_path):
            os.unlink(checkpoint_path)
            print(f"🗑️  Checkpoint file deleted (clean completion)\n")
        
        return merged_delta
    
    def ingest_directory(self, dir_path: str, engine: IngestionEngine) -> List[Dict[str, Any]]:
        """
        Ingest all ChatGPT JSON files from a directory.
        
        Args:
            dir_path: Path to directory containing ChatGPT JSON export files
            engine: Initialized IngestionEngine instance
            
        Returns:
            List of TruthDelta dicts, one per file
        """
        dir_path = Path(dir_path)
        if not dir_path.is_dir():
            raise NotADirectoryError(f"{dir_path} is not a directory")
        
        # Find all .json files
        json_files = sorted(dir_path.glob('*.json'))
        
        if not json_files:
            print(f"No JSON files found in {dir_path}")
            return []
        
        print(f"Found {len(json_files)} JSON files in {dir_path}")
        print()
        
        deltas = []
        for i, json_file in enumerate(json_files, 1):
            print(f"[{i}/{len(json_files)}] Processing {json_file.name}")
            try:
                delta = self.ingest_file(str(json_file), engine)
                deltas.append(delta)
            except Exception as e:
                print(f"  ✗ Error processing {json_file.name}: {e}")
                continue
            print()
        
        # Summary
        total_nodes = sum(len(d['nodes_added']) for d in deltas)
        total_edges = sum(len(d['edges_added']) for d in deltas)
        total_weights = sum(len(d['weights_added']) for d in deltas)
        
        print("=" * 60)
        print(f"✓ Ingestion complete!")
        print(f"  Files processed: {len(deltas)}/{len(json_files)}")
        print(f"  Total nodes added: {total_nodes}")
        print(f"  Total edges added: {total_edges}")
        print(f"  Total weights added: {total_weights}")
        print("=" * 60)
        
        return deltas
