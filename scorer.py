"""
Challenge scoring and quality assurance module
"""

import logging
import re
from typing import Dict, List
from config import (
    CHALLENGE_KEYWORDS_EN, CHALLENGE_KEYWORDS_NL,
    SOLUTION_KEYWORDS_EN, SOLUTION_KEYWORDS_NL,
    CHALLENGE_DENSITY_WEIGHT, SPECIFICITY_WEIGHT, EVIDENCE_WEIGHT,
    RECENCY_WEIGHT, SOLUTION_LEAKAGE_WEIGHT
)

logger = logging.getLogger(__name__)


class ChallengeScorer:
    """Score challenges based on quality metrics"""
    
    def __init__(self):
        self.challenge_keywords = CHALLENGE_KEYWORDS_EN | CHALLENGE_KEYWORDS_NL
        self.solution_keywords = SOLUTION_KEYWORDS_EN | SOLUTION_KEYWORDS_NL
        
    def score_challenge(self, challenge: Dict) -> Dict:
        """Score a single challenge"""
        statement = challenge.get('challenge_statement', '')
        
        # Calculate individual scores
        challenge_density = self._score_challenge_density(statement)
        solution_leakage = self._score_solution_leakage(statement)
        specificity = self._score_specificity(challenge)
        evidence_strength = self._score_evidence(challenge)
        recency_score = self._score_recency(challenge)
        
        # Calculate overall score
        overall_score = (
            CHALLENGE_DENSITY_WEIGHT * challenge_density +
            SPECIFICITY_WEIGHT * specificity +
            EVIDENCE_WEIGHT * evidence_strength +
            RECENCY_WEIGHT * recency_score +
            SOLUTION_LEAKAGE_WEIGHT * solution_leakage
        )
        
        # Clamp to 0-100
        overall_score = max(0, min(100, overall_score))
        
        return {
            'challenge_density': int(challenge_density),
            'solution_leakage': int(solution_leakage),
            'specificity': int(specificity),
            'evidence_strength': int(evidence_strength),
            'recency_score': int(recency_score),
            'overall_score': int(overall_score),
            'scoring_notes': f"Density: {challenge_density:.0f}, Solution leakage: {solution_leakage:.0f}, Specificity: {specificity:.0f}"
        }
        
    def score_batch(self, challenges: List[Dict]) -> List[Dict]:
        """Score multiple challenges"""
        scored = []
        
        for challenge in challenges:
            score = self.score_challenge(challenge)
            challenge['score'] = score
            scored.append(challenge)
            
        logger.info(f"Scored {len(scored)} challenges")
        return scored
        
    def _score_challenge_density(self, text: str) -> float:
        """Score based on challenge keyword density"""
        if not text:
            return 0.0
            
        text_lower = text.lower()
        word_count = len(text.split())
        
        # Count challenge keywords
        challenge_count = sum(1 for keyword in self.challenge_keywords if keyword in text_lower)
        
        if word_count == 0:
            return 0.0
            
        # Normalize: challenge_count / word_count * 100
        density = (challenge_count / word_count) * 100
        
        # Scale to 0-100 (assume max density is 10%)
        score = min(100, density * 10)
        
        return score
        
    def _score_solution_leakage(self, text: str) -> float:
        """Score solution language (higher = more solution talk)"""
        if not text:
            return 0.0
            
        text_lower = text.lower()
        word_count = len(text.split())
        
        # Count solution keywords
        solution_count = sum(1 for keyword in self.solution_keywords if keyword in text_lower)
        
        if word_count == 0:
            return 0.0
            
        # Normalize
        leakage = (solution_count / word_count) * 100
        
        # Scale to 0-100
        score = min(100, leakage * 10)
        
        return score
        
    def _score_specificity(self, challenge: Dict) -> float:
        """Score specificity based on presence of numbers, geographies, target groups"""
        score = 0.0
        
        # Check for numbers in scale_numbers
        if challenge.get('scale_numbers'):
            score += 30
            
        # Check for geography
        if challenge.get('geography'):
            score += 30
            
        # Check for target groups
        if challenge.get('target_groups') and len(challenge['target_groups']) > 0:
            score += 20
            
        # Check for sectors
        if challenge.get('sectors') and len(challenge['sectors']) > 0:
            score += 20
            
        return min(100, score)
        
    def _score_evidence(self, challenge: Dict) -> float:
        """Score evidence strength"""
        score = 0.0
        
        # Evidence quotes
        if challenge.get('evidence_quotes') and len(challenge['evidence_quotes']) > 0:
            score += 40
            
        # Root causes
        if challenge.get('root_causes') and len(challenge['root_causes']) > 0:
            score += 30
            
        # Constraints
        if challenge.get('constraints') and len(challenge['constraints']) > 0:
            score += 30
            
        return min(100, score)
        
    def _score_recency(self, challenge: Dict) -> float:
        """Score based on recency (simplified: assume recent if extracted recently)"""
        # For MVP, assume all recently extracted challenges are recent
        # In production, parse dates from source documents
        return 70.0
        
    def filter_challenges(self, challenges: List[Dict], 
                         min_overall_score: int = 40,
                         min_confidence: float = 0.50,
                         max_solution_leakage: int = 70) -> List[Dict]:
        """Filter challenges based on quality thresholds"""
        filtered = []
        
        for challenge in challenges:
            score = challenge.get('score', {})
            confidence = challenge.get('confidence', 0)
            
            if (score.get('overall_score', 0) >= min_overall_score and
                confidence >= min_confidence and
                score.get('solution_leakage', 0) <= max_solution_leakage):
                filtered.append(challenge)
                
        logger.info(f"Filtered to {len(filtered)} challenges (from {len(challenges)})")
        return filtered
