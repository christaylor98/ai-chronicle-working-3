"""
Text parsing and atomic unit extraction from raw content.
"""

import re
from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class ExtractedUnit:
    """Raw extracted semantic unit before validation."""
    
    text: str
    span: Tuple[int, int]  # Character range in source
    context: str  # Surrounding text for context


class TextParser:
    """
    Parses raw text into candidate atomic units.
    
    Extraction strategies:
    - Sentence-level decomposition
    - Bullet point extraction
    - Statement identification within paragraphs
    """
    
    def __init__(self):
        self.sentence_boundary = re.compile(r'[.!?]+\s+')
        self.bullet_pattern = re.compile(r'^\s*[-•*]\s+', re.MULTILINE)
    
    def parse(self, content: str) -> List[ExtractedUnit]:
        """
        Extract candidate atomic units from raw content.
        
        Returns:
            List of extracted units with their source spans
        """
        units = []
        
        # Strategy 1: Extract bullet points first (often atomic)
        units.extend(self._extract_bullets(content))
        
        # Strategy 2: Extract numbered lists
        units.extend(self._extract_numbered_lists(content))
        
        # Strategy 3: Split remaining text into sentences
        units.extend(self._extract_sentences(content))
        
        # Deduplicate by span (avoid overlaps)
        units = self._deduplicate_by_span(units)
        
        return units
    
    def _extract_bullets(self, content: str) -> List[ExtractedUnit]:
        """Extract bullet-pointed items."""
        units = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            if self.bullet_pattern.match(line):
                # Clean bullet marker
                text = self.bullet_pattern.sub('', line).strip()
                
                if len(text) > 10:  # Minimum length
                    # Find span in original content
                    start = content.find(line)
                    end = start + len(line)
                    
                    # Get context (previous and next lines)
                    context_lines = lines[max(0, i-1):min(len(lines), i+2)]
                    context = '\n'.join(context_lines)
                    
                    units.append(ExtractedUnit(
                        text=text,
                        span=(start, end),
                        context=context
                    ))
        
        return units
    
    def _extract_numbered_lists(self, content: str) -> List[ExtractedUnit]:
        """Extract numbered list items."""
        units = []
        pattern = re.compile(r'^\s*\d+\.\s+(.+)$', re.MULTILINE)
        
        for match in pattern.finditer(content):
            text = match.group(1).strip()
            
            if len(text) > 10:
                units.append(ExtractedUnit(
                    text=text,
                    span=(match.start(), match.end()),
                    context=content[max(0, match.start()-100):match.end()+100]
                ))
        
        return units
    
    def _extract_sentences(self, content: str) -> List[ExtractedUnit]:
        """Extract sentence-level units from prose."""
        units = []
        
        # Split on sentence boundaries
        sentences = self.sentence_boundary.split(content)
        
        pos = 0
        for sentence in sentences:
            sentence = sentence.strip()
            
            if len(sentence) > 10:  # Minimum length
                # Find actual position in content
                start = content.find(sentence, pos)
                end = start + len(sentence)
                
                # Get context window
                context_start = max(0, start - 100)
                context_end = min(len(content), end + 100)
                context = content[context_start:context_end]
                
                units.append(ExtractedUnit(
                    text=sentence,
                    span=(start, end),
                    context=context
                ))
                
                pos = end
        
        return units
    
    def _deduplicate_by_span(self, units: List[ExtractedUnit]) -> List[ExtractedUnit]:
        """Remove overlapping units, preferring more specific ones."""
        if not units:
            return []
        
        # Sort by span start, then by length (shorter = more specific)
        sorted_units = sorted(units, key=lambda u: (u.span[0], u.span[1] - u.span[0]))
        
        deduplicated = []
        last_end = -1
        
        for unit in sorted_units:
            # Skip if overlaps with previous unit
            if unit.span[0] < last_end:
                continue
            
            deduplicated.append(unit)
            last_end = unit.span[1]
        
        return deduplicated
    
    def extract_key_terms(self, text: str, max_terms: int = 5) -> List[str]:
        """
        Extract canonical terms from text for indexing.
        
        Simple heuristic: extract capitalized words and longer words.
        """
        # Find capitalized words (potential named entities)
        capitalized = re.findall(r'\b[A-Z][a-z]+\b', text)
        
        # Find longer words (likely content-bearing)
        words = re.findall(r'\b\w+\b', text.lower())
        long_words = [w for w in words if len(w) > 6]
        
        # Combine and deduplicate
        terms = list(dict.fromkeys(capitalized + long_words))
        
        return terms[:max_terms]
