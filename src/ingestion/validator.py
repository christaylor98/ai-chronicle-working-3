"""
Atomicity validation - ensures extracted units meet self-containment requirements.
"""

import re
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class AtomicityViolation:
    """Describes why a statement fails atomicity test."""
    
    rule: str
    description: str
    suggestion: str


class AtomicityValidator:
    """
    Validates that statements meet atomicity requirements.
    
    Atomicity tests:
    1. Statement is self-contained
    2. Statement does not rely on external pronouns
    3. Statement expresses one claim
    4. Statement is not redundant (checked separately via similarity)
    """
    
    # Dependency pronouns that often indicate non-self-containment
    DEPENDENCY_PRONOUNS = {
        "this", "that", "it", "they", "these", "those", 
        "he", "she", "him", "her", "them"
    }
    
    # Multi-claim indicators
    MULTI_CLAIM_PATTERNS = [
        r"\b(and|or)\b.*\b(and|or)\b",  # Multiple conjunctions
        r";\s*\w+",  # Semicolon-separated clauses
        r"\.\s+\w+",  # Multiple sentences
    ]
    
    def __init__(self, strict: bool = True):
        """
        Initialize validator.
        
        Args:
            strict: If True, enforce stricter rules
        """
        self.strict = strict
    
    def validate(self, statement: str) -> Tuple[bool, List[AtomicityViolation]]:
        """
        Validate statement atomicity.
        
        Returns:
            (is_valid, violations)
        """
        violations = []
        
        # Test 1: Self-containment (pronoun dependency check)
        pronoun_violation = self._check_pronoun_dependency(statement)
        if pronoun_violation:
            violations.append(pronoun_violation)
        
        # Test 2: Single claim
        multi_claim_violation = self._check_single_claim(statement)
        if multi_claim_violation:
            violations.append(multi_claim_violation)
        
        # Test 3: Minimum length
        length_violation = self._check_minimum_length(statement)
        if length_violation:
            violations.append(length_violation)
        
        # Test 4: Contains meaningful content
        content_violation = self._check_meaningful_content(statement)
        if content_violation:
            violations.append(content_violation)
        
        return len(violations) == 0, violations
    
    def _check_pronoun_dependency(self, statement: str) -> Optional[AtomicityViolation]:
        """Check for dependency pronouns suggesting external context."""
        words = statement.lower().split()
        
        if not words:
            return AtomicityViolation(
                rule="SELF_CONTAINMENT",
                description="Statement is empty",
                suggestion="Provide a complete statement"
            )
        
        # Check if starts with dependency pronoun
        first_word = words[0].strip(".,;:!?")
        if first_word in self.DEPENDENCY_PRONOUNS:
            return AtomicityViolation(
                rule="SELF_CONTAINMENT",
                description=f"Statement starts with dependency pronoun '{first_word}'",
                suggestion="Replace pronoun with explicit subject"
            )
        
        # In strict mode, flag high pronoun density
        if self.strict:
            pronoun_count = sum(1 for word in words if word in self.DEPENDENCY_PRONOUNS)
            if len(words) > 0 and pronoun_count / len(words) > 0.25:
                return AtomicityViolation(
                    rule="SELF_CONTAINMENT",
                    description="High pronoun density suggests context dependency",
                    suggestion="Make references explicit"
                )
        
        return None
    
    def _check_single_claim(self, statement: str) -> Optional[AtomicityViolation]:
        """Check if statement expresses single claim."""
        # Check for multiple sentences
        sentence_count = len(re.findall(r'[.!?]+\s+[A-Z]', statement))
        if sentence_count > 0:
            return AtomicityViolation(
                rule="SINGLE_CLAIM",
                description="Statement contains multiple sentences",
                suggestion="Split into separate atomic statements"
            )
        
        # Check for complex conjunctions
        for pattern in self.MULTI_CLAIM_PATTERNS:
            if re.search(pattern, statement):
                return AtomicityViolation(
                    rule="SINGLE_CLAIM",
                    description="Statement appears to contain multiple claims",
                    suggestion="Split into separate atomic statements"
                )
        
        return None
    
    def _check_minimum_length(self, statement: str) -> Optional[AtomicityViolation]:
        """Check minimum length requirement."""
        if len(statement.strip()) < 10:
            return AtomicityViolation(
                rule="MINIMUM_LENGTH",
                description="Statement too short to be meaningful",
                suggestion="Provide more complete statement"
            )
        return None
    
    def _check_meaningful_content(self, statement: str) -> Optional[AtomicityViolation]:
        """Check that statement contains meaningful content."""
        # Remove common stop words and check if substance remains
        words = statement.lower().split()
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for"}
        content_words = [w for w in words if w not in stop_words]
        
        if len(content_words) < 3:
            return AtomicityViolation(
                rule="MEANINGFUL_CONTENT",
                description="Statement lacks sufficient semantic content",
                suggestion="Provide more substantive claim"
            )
        
        return None
    
    def suggest_repair(self, statement: str, context: str = "") -> List[str]:
        """
        Suggest potential repairs for non-atomic statement.
        
        Args:
            statement: The problematic statement
            context: Optional surrounding context for pronoun resolution
        
        Returns:
            List of suggested atomic statements
        """
        is_valid, violations = self.validate(statement)
        if is_valid:
            return [statement]
        
        suggestions = []
        
        # If multiple sentences, split them
        sentences = re.split(r'[.!?]+\s+', statement)
        if len(sentences) > 1:
            suggestions.extend([s.strip() + "." for s in sentences if s.strip()])
        
        # If starts with pronoun and context provided, attempt resolution
        words = statement.split()
        if words and words[0].lower() in self.DEPENDENCY_PRONOUNS and context:
            # Simple heuristic: try to extract subject from context
            context_words = context.split()
            # Look for capitalized words (potential subjects)
            subjects = [w for w in context_words if w[0].isupper() and len(w) > 1]
            if subjects:
                suggested = f"{subjects[-1]} " + " ".join(words[1:])
                suggestions.append(suggested)
        
        return suggestions if suggestions else [statement]
