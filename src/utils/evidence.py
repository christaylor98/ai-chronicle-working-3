"""
Provenance and evidence tracking utilities.
"""

from datetime import datetime
from typing import Dict, List, Optional
from src.core.node import Evidence


class ProvenanceTracker:
    """
    Tracks evidence chains and source attribution for all graph additions.
    """
    
    def __init__(self):
        self.records: List[Dict] = []
    
    def record_ingestion(
        self,
        context_node_id: str,
        source_file: str,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict] = None,
    ) -> str:
        """
        Record an ingestion event.
        
        Returns:
            Record ID for reference
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        record = {
            "record_id": f"prov_{len(self.records):06d}",
            "context_node_id": context_node_id,
            "source_file": source_file,
            "ingestion_timestamp": timestamp.isoformat(),
            "metadata": metadata or {},
        }
        
        self.records.append(record)
        return record["record_id"]
    
    def create_evidence(
        self,
        source: str,
        span: Optional[tuple[int, int]] = None,
        confidence: float = 1.0,
    ) -> Evidence:
        """Create evidence pointer with validation."""
        return Evidence(source=source, span=span, confidence=confidence)
    
    def get_provenance(self) -> List[Dict]:
        """Export all provenance records."""
        return self.records
    
    def clear(self) -> None:
        """Clear all records (use with caution)."""
        self.records = []
