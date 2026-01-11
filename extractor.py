"""
LLM-based challenge extraction module
"""

import json
import logging
from typing import List, Dict, Optional
from openai import OpenAI
from config import LLM_MODEL, LLM_TEMPERATURE

logger = logging.getLogger(__name__)

# Initialize OpenAI client (uses OPENAI_API_KEY from environment)
client = OpenAI()


EXTRACTOR_PROMPT = """ROLE: SDG Challenge Extractor (problem-first, no solutions).

INPUT:
- source_org: {org_name}
- source_url: {url}
- text_chunk: {chunk}

TASK:
Extract ONLY challenges (problem statements) from the chunk.
A challenge is a statement describing: unmet needs, barriers, gaps, risks, constraints, vulnerable groups, capacity limitations, governance/infrastructure/finance/data constraints.

OUTPUT JSON (array of objects):
[{{
  "challenge_title": "...",
  "challenge_statement": "...",         // 1-2 sentences, no solution language
  "sdg_goals": [..],                    // empty if unsure
  "geography": "...",
  "target_groups": [".."],
  "sectors": [".."],
  "scale_numbers": {{"...": ...}},        // only if present
  "root_causes": [".."],
  "constraints": [".."],
  "evidence_quotes": ["..", ".."],      // max 2, <=20 words each
  "confidence": 0.00-1.00
}}]

RULES:
- Do NOT describe interventions, technologies, programs, or "what they will do".
- If the chunk is solution-heavy, infer the underlying problem briefly and lower confidence.
- Prefer challenges that are specific and testable over generic statements.
- Return [] if no challenges are present.

Return ONLY valid JSON, no other text."""


class ChallengeExtractor:
    """Extract challenges from text using LLM"""
    
    def __init__(self, model: str = LLM_MODEL):
        self.model = model
        self.client = client
        
    def extract_challenges(self, chunk: str, org_name: str, url: str) -> List[Dict]:
        """Extract challenges from a text chunk"""
        if not chunk or len(chunk.strip()) < 50:
            logger.debug("Chunk too short to extract")
            return []
            
        prompt = EXTRACTOR_PROMPT.format(
            org_name=org_name,
            url=url,
            chunk=chunk[:3000]  # Limit chunk size for API
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert in identifying SDG-related challenges and problems. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=LLM_TEMPERATURE,
                max_tokens=2000
            )
            
            # Parse response
            response_text = response.choices[0].message.content.strip()
            
            # Try to extract JSON from response
            try:
                challenges = json.loads(response_text)
            except json.JSONDecodeError:
                # Try to find JSON in response
                import re
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    challenges = json.loads(json_match.group())
                else:
                    logger.warning(f"Could not parse LLM response: {response_text[:200]}")
                    return []
            
            if not isinstance(challenges, list):
                challenges = [challenges]
                
            logger.info(f"Extracted {len(challenges)} challenges from chunk")
            return challenges
            
        except Exception as e:
            logger.error(f"Error extracting challenges: {e}")
            return []
            
    def extract_batch(self, chunks: List[Dict], org_name: str, url: str) -> List[Dict]:
        """Extract challenges from multiple chunks"""
        all_challenges = []
        
        for i, chunk_data in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)}")
            challenges = self.extract_challenges(
                chunk_data["text"],
                org_name,
                url
            )
            
            # Add metadata to each challenge
            for challenge in challenges:
                challenge["chunk_index"] = chunk_data.get("index", i)
                challenge["source_url"] = url
                challenge["source_org"] = org_name
                
            all_challenges.extend(challenges)
            
        return all_challenges
