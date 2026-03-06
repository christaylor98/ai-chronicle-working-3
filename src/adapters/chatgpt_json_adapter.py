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
    
    def ingest_file(self, file_path: str, engine: IngestionEngine) -> Dict[str, Any]:
        """
        Ingest a single ChatGPT JSON file into the knowledge graph.
        
        Args:
            file_path: Path to the ChatGPT JSON export file
            engine: Initialized IngestionEngine instance
            
        Returns:
            Merged TruthDelta from all ingested chunks
        """
        print(f"Parsing ChatGPT conversation file: {file_path}")
        chunks = self.parse_conversation(file_path)
        
        if not chunks:
            print(f"  No assistant messages found in {file_path}")
            return {
                'nodes_added': [],
                'edges_added': [],
                'weights_added': []
            }
        
        print(f"  Found {len(chunks)} assistant messages")
        
        # Merge all truth deltas
        merged_delta = {
            'nodes_added': [],
            'edges_added': [],
            'weights_added': []
        }
        
        # Process each chunk
        for i, chunk in enumerate(chunks, 1):
            # Create temporary file for this chunk
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as tmp_file:
                tmp_file.write(chunk.text)
                tmp_path = tmp_file.name
            
            try:
                # Prepare metadata with timestamp and conversation info
                metadata = {
                    'timestamp': chunk.timestamp,
                    'conversation_id': chunk.conversation_id,
                    'message_id': chunk.message_id,
                    'source_type': 'chatgpt_conversation'
                }
                if chunk.conversation_title:
                    metadata['conversation_title'] = chunk.conversation_title
                
                # Ingest through existing pipeline
                truth_delta = engine.ingest_file(tmp_path, metadata=metadata)
                
                # Merge results
                merged_delta['nodes_added'].extend(truth_delta['nodes_added'])
                merged_delta['edges_added'].extend(truth_delta['edges_added'])
                merged_delta['weights_added'].extend(truth_delta['weights_added'])
                
                if i % 10 == 0:
                    print(f"    Processed {i}/{len(chunks)} messages...")
                
            finally:
                # Clean up temp file
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
        
        print(f"  ✓ Ingested {len(chunks)} messages")
        print(f"    Nodes added: {len(merged_delta['nodes_added'])}")
        print(f"    Edges added: {len(merged_delta['edges_added'])}")
        print(f"    Weights added: {len(merged_delta['weights_added'])}")
        
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
