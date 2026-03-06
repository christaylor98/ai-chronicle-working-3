"""
Text parsing and atomic unit extraction from raw content.
"""

import re
import json
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
    
    Meta-content filtering:
    - Remove docstrings (triple quotes)
    - Remove line comments
    - Remove markdown headers
    """
    
    def __init__(self):
        self.sentence_boundary = re.compile(r'[.!?]+\s+')
        self.bullet_pattern = re.compile(r'^\s*[-•*]\s+', re.MULTILINE)
        
        # Meta-content patterns
        self.docstring_pattern = re.compile(r'"""[\s\S]*?"""|\'\'\'\'[\s\S]*?\'\'\'\'')
        self.line_comment_pattern = re.compile(r'^\s*#.*$', re.MULTILINE)
        self.markdown_header_pattern = re.compile(r'^\s*#+\s+.*$', re.MULTILINE)
    
    def parse(self, content: str) -> List[ExtractedUnit]:
        """
        Extract candidate atomic units from raw content.
        
        Returns:
            List of extracted units with their source spans
        """
        # Step 1: Filter meta-content BEFORE extraction
        filtered_content, span_map = self._filter_meta_content(content)
        
        units = []
        
        # Strategy 1: Extract bullet points first (often atomic)
        units.extend(self._extract_bullets(filtered_content))
        
        # Strategy 2: Extract numbered lists
        units.extend(self._extract_numbered_lists(filtered_content))
        
        # Strategy 3: Split remaining text into sentences
        units.extend(self._extract_sentences(filtered_content))
        
        # Deduplicate by span (avoid overlaps)
        units = self._deduplicate_by_span(units)
        
        # Remap spans to original content positions
        units = self._remap_spans(units, span_map, content)
        
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
    
    def _filter_meta_content(self, content: str) -> Tuple[str, List[Tuple[int, int]]]:
        """
        Remove meta-content (docstrings, comments, headers) before extraction.
        
        Returns:
            (filtered_content, span_map) where span_map tracks removed regions
        """
        filtered = content
        removed_spans = []
        
        # Remove docstrings
        for match in self.docstring_pattern.finditer(content):
            start, end = match.span()
            removed_spans.append((start, end))
        filtered = self.docstring_pattern.sub('', filtered)
        
        # Remove line comments
        filtered = self.line_comment_pattern.sub('', filtered)
        
        # Remove markdown headers
        filtered = self.markdown_header_pattern.sub('', filtered)
        
        return filtered, removed_spans
    
    def _remap_spans(self, units: List[ExtractedUnit], span_map: List[Tuple[int, int]], original: str) -> List[ExtractedUnit]:
        """
        Remap spans from filtered content back to original content positions.
        """
        # For now, recalculate spans in original content
        remapped = []
        for unit in units:
            # Find text in original content
            try:
                start = original.find(unit.text)
                if start != -1:
                    end = start + len(unit.text)
                    remapped.append(ExtractedUnit(
                        text=unit.text,
                        span=(start, end),
                        context=unit.context
                    ))
            except:
                # Skip if can't remap
                pass
        return remapped
    
    def extract_key_terms(self, text: str, max_terms: int = 5) -> List[str]:
        """
        Extract canonical terms from text for indexing.
        
        Filters stopwords and articles per INGESTION_CORRECTION_SPEC.v1.0.
        """
        # Stopwords to exclude
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
            'that', 'these', 'those', 'it', 'its', 'they', 'them', 'their'
        }
        
        # Find capitalized words (potential named entities)
        capitalized = re.findall(r'\b[A-Z][a-z]+\b', text)
        
        # Find longer words (likely content-bearing)
        words = re.findall(r'\b\w+\b', text.lower())
        long_words = [w for w in words if len(w) > 6 and w not in stopwords]
        
        # Combine and deduplicate, filtering stopwords
        all_terms = capitalized + long_words
        terms = [t for t in dict.fromkeys(all_terms) if t.lower() not in stopwords]
        
        return terms[:max_terms]
