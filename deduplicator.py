"""
Deduplication and fingerprinting module
"""

import hashlib
import logging
import re
from typing import List, Dict, Optional
from nltk.corpus import stopwords

logger = logging.getLogger(__name__)

# Download stopwords if needed (for production, do this once)
try:
    stopwords.words('english')
except LookupError:
    import nltk
    nltk.download('stopwords')


class Deduplicator:
    """Handle challenge deduplication and fingerprinting"""
    
    def __init__(self):
        self.en_stopwords = set(stopwords.words('english'))
        self.nl_stopwords = set(stopwords.words('dutch'))
        self.all_stopwords = self.en_stopwords | self.nl_stopwords
        
    def create_fingerprint(self, text: str) -> str:
        """Create a normalized fingerprint of text"""
        # Lowercase
        text = text.lower()
        
        # Remove punctuation
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove stopwords
        words = [w for w in text.split() if w not in self.all_stopwords]
        
        # Normalize numbers
        text = ' '.join(words)
        text = re.sub(r'\d+', '<num>', text)
        
        # Create hash
        fingerprint = hashlib.sha256(text.encode()).hexdigest()
        return fingerprint
        
    def find_duplicates(self, challenges: List[Dict]) -> List[List[int]]:
        """Find groups of duplicate challenges by fingerprint"""
        fingerprint_map = {}
        
        for i, challenge in enumerate(challenges):
            statement = challenge.get('challenge_statement', '')
            if not statement:
                continue
                
            fp = self.create_fingerprint(statement)
            
            if fp not in fingerprint_map:
                fingerprint_map[fp] = []
            fingerprint_map[fp].append(i)
            
        # Return only groups with duplicates
        return [indices for indices in fingerprint_map.values() if len(indices) > 1]
        
    def merge_duplicates(self, challenges: List[Dict], duplicate_groups: List[List[int]]) -> List[Dict]:
        """Merge duplicate challenges, keeping best evidence"""
        merged = list(challenges)
        indices_to_remove = set()
        
        for group in duplicate_groups:
            if len(group) < 2:
                continue
                
            # Sort by confidence (highest first)
            group_sorted = sorted(group, key=lambda i: challenges[i].get('confidence', 0), reverse=True)
            
            # Keep the first (highest confidence)
            primary_idx = group_sorted[0]
            primary = merged[primary_idx]
            
            # Merge evidence from others
            all_quotes = set(primary.get('evidence_quotes', []))
            all_causes = set(primary.get('root_causes', []))
            all_constraints = set(primary.get('constraints', []))
            
            for idx in group_sorted[1:]:
                if idx < len(challenges):
                    other = challenges[idx]
                    all_quotes.update(other.get('evidence_quotes', []))
                    all_causes.update(other.get('root_causes', []))
                    all_constraints.update(other.get('constraints', []))
                    indices_to_remove.add(idx)
            
            # Update primary with merged data
            primary['evidence_quotes'] = list(all_quotes)[:2]  # Keep max 2
            primary['root_causes'] = list(all_causes)
            primary['constraints'] = list(all_constraints)
            primary['merged_from'] = len(group)
            
        # Remove duplicates
        result = [c for i, c in enumerate(merged) if i not in indices_to_remove]
        logger.info(f"Merged {len(indices_to_remove)} duplicate challenges")
        
        return result
        
    def add_fingerprints(self, challenges: List[Dict]) -> List[Dict]:
        """Add fingerprints to all challenges"""
        for challenge in challenges:
            statement = challenge.get('challenge_statement', '')
            if statement:
                challenge['statement_fingerprint'] = self.create_fingerprint(statement)
                
        return challenges
