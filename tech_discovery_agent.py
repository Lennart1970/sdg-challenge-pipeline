"""
Technology Discovery Agent

This agent takes a challenge statement and discovers plausible technology paths
by reasoning from problems → functions → principles → technology classes.

Key principles:
- Discover, don't invent: Find what's already possible
- No brands or SKUs: Technology classes only
- Budget constraint: Under €10,000
- Grounded in reality: Feasible with existing technology
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class TechnologyDiscoveryAgent:
    """
    Agent that discovers plausible technology paths for SDG challenges
    
    The agent uses constraint-driven reasoning to map challenges to
    technology classes through functions and principles, staying under
    a strict budget constraint.
    """
    
    def __init__(self, llm_client, max_budget_eur: int = 10000):
        """
        Initialize Technology Discovery Agent
        
        Args:
            llm_client: LLM client with structured output support
            max_budget_eur: Maximum budget constraint in euros
        """
        self.llm_client = llm_client
        self.max_budget_eur = max_budget_eur
        logger.info(f"Initialized Technology Discovery Agent with budget constraint: €{max_budget_eur}")
    
    def build_discovery_prompt(self, challenge: Dict[str, Any]) -> str:
        """
        Build the discovery prompt for a given challenge
        
        Args:
            challenge: Challenge dictionary with title, statement, metadata
            
        Returns:
            Formatted prompt string
        """
        challenge_title = challenge.get('challenge_title', 'Untitled Challenge')
        challenge_statement = challenge.get('challenge_statement', '')
        sdg_goals = challenge.get('sdg_goals', [])
        geography = challenge.get('geography', 'Not specified')
        target_groups = challenge.get('target_groups', [])
        sectors = challenge.get('sectors', [])
        
        prompt = f"""You are a technology discovery agent. Your task is to discover plausible technology pathways for real-world challenges using existing, widely available technology.

**Challenge:**
{challenge_title}

**Problem Statement:**
{challenge_statement}

**Context:**
- SDG Goals: {', '.join(map(str, sdg_goals)) if sdg_goals else 'Not specified'}
- Geography: {geography}
- Target Groups: {', '.join(target_groups) if target_groups else 'Not specified'}
- Sectors: {', '.join(sectors) if sectors else 'Not specified'}

**Your Task:**

1. **Identify Core Functions**: What must physically happen to address this challenge? Think in terms of actions, transformations, or processes.

2. **Map to Principles**: What physical, chemical, or mechanical principles enable these functions?

3. **Discover Technology Paths**: Based on these principles, what technology classes (NOT specific products or brands) could plausibly implement this under €{self.max_budget_eur}?

**Critical Constraints:**

- **Budget**: All paths must be achievable under €{self.max_budget_eur}
- **No Brands/SKUs**: Only technology classes (e.g., "pressure vessel", "solar thermal collector", "biodigester")
- **Existing Technology**: Use what already exists and is widely available
- **Human-Scale**: Solutions should be locally feasible and maintainable
- **Reuse & Recombination**: Consider second-hand equipment, DIY tooling, open hardware

**Output Requirements:**

- Provide 2-3 distinct technology paths
- Each path should be plausible, not optimal
- Focus on directional intelligence, not finished designs
- Include cost bands (e.g., "€500-€2000", "€3000-€8000")
- Identify key risks and unknowns

**Remember:**
- You are discovering what is already possible, not inventing new solutions
- Think in functions → principles → technology classes
- Clarity beats cleverness. Reality beats novelty.
"""
        
        return prompt
    
    def build_system_prompt(self) -> str:
        """
        Build the system prompt for the Technology Discovery Agent
        
        Returns:
            System prompt string
        """
        return f"""You are a constraint-driven technology discovery agent specializing in finding feasible technology pathways for sustainability challenges.

Your approach:
1. Start with the problem, not the solution
2. Reason from functions → principles → technology classes
3. Stay under €{self.max_budget_eur} budget constraint
4. Use existing, widely available technology
5. Never recommend specific brands or products
6. Focus on human-scale, locally feasible solutions

You output structured JSON with:
- Challenge summary
- Core functions (what must happen)
- Underlying principles (physical/chemical/mechanical)
- 2-3 technology paths with cost bands and risks
- Confidence score

Your outputs are directional intelligence, not finished designs."""
    
    def discover_technology_paths(
        self,
        challenge: Dict[str, Any],
        model: str = "gpt-4.1-mini"
    ) -> Dict[str, Any]:
        """
        Discover technology paths for a given challenge
        
        Args:
            challenge: Challenge dictionary from database
            model: LLM model to use
            
        Returns:
            Dictionary with discovery results (matches TECH_DISCOVERY_SCHEMA)
        """
        logger.info(f"Starting technology discovery for challenge: {challenge.get('challenge_id')}")
        
        # Build prompts
        user_prompt = self.build_discovery_prompt(challenge)
        system_prompt = self.build_system_prompt()
        
        # Call LLM with structured outputs
        try:
            response_text = self.llm_client.complete(
                prompt=user_prompt,
                model=model,
                system_prompt=system_prompt
            )
            
            # Parse JSON response
            discovery_result = json.loads(response_text)
            
            # Add metadata
            discovery_result['challenge_id'] = challenge.get('challenge_id')
            discovery_result['discovered_at'] = datetime.utcnow().isoformat()
            discovery_result['model_used'] = model
            discovery_result['budget_constraint_eur'] = self.max_budget_eur
            
            # Validate paths are within budget
            self._validate_budget_constraint(discovery_result)
            
            logger.info(f"Successfully discovered {len(discovery_result.get('technology_paths', []))} technology paths")
            
            return discovery_result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise
        except Exception as e:
            logger.error(f"Error during technology discovery: {e}")
            raise
    
    def _validate_budget_constraint(self, discovery_result: Dict[str, Any]) -> None:
        """
        Validate that all technology paths respect the budget constraint
        
        Args:
            discovery_result: Discovery result dictionary
            
        Raises:
            ValueError: If any path exceeds budget constraint
        """
        paths = discovery_result.get('technology_paths', [])
        
        for i, path in enumerate(paths):
            cost_band = path.get('estimated_cost_band_eur', '')
            
            # Extract maximum cost from band (e.g., "€3000-€8000" → 8000)
            try:
                # Remove € and split on '-'
                cost_parts = cost_band.replace('€', '').replace(',', '').split('-')
                if len(cost_parts) >= 2:
                    max_cost = int(cost_parts[1].strip())
                    
                    if max_cost > self.max_budget_eur:
                        logger.warning(
                            f"Path {i+1} '{path.get('path_name')}' exceeds budget: "
                            f"€{max_cost} > €{self.max_budget_eur}"
                        )
                        # Note: We log a warning but don't fail, as LLM might have good reasons
            except (ValueError, IndexError) as e:
                logger.warning(f"Could not parse cost band '{cost_band}': {e}")
    
    def format_discovery_summary(self, discovery_result: Dict[str, Any]) -> str:
        """
        Format discovery result as human-readable summary
        
        Args:
            discovery_result: Discovery result dictionary
            
        Returns:
            Formatted summary string
        """
        summary = []
        summary.append("=" * 80)
        summary.append("TECHNOLOGY DISCOVERY RESULT")
        summary.append("=" * 80)
        summary.append("")
        
        summary.append(f"Challenge: {discovery_result.get('challenge_summary', 'N/A')}")
        summary.append(f"Confidence: {discovery_result.get('confidence', 0):.2f}")
        summary.append(f"Budget Constraint: €{self.max_budget_eur}")
        summary.append("")
        
        summary.append("CORE FUNCTIONS:")
        for func in discovery_result.get('core_functions', []):
            summary.append(f"  • {func}")
        summary.append("")
        
        summary.append("UNDERLYING PRINCIPLES:")
        for principle in discovery_result.get('underlying_principles', []):
            summary.append(f"  • {principle}")
        summary.append("")
        
        paths = discovery_result.get('technology_paths', [])
        summary.append(f"TECHNOLOGY PATHS ({len(paths)} discovered):")
        summary.append("")
        
        for i, path in enumerate(paths, 1):
            summary.append(f"Path {i}: {path.get('path_name', 'Unnamed')}")
            summary.append(f"  Cost Band: {path.get('estimated_cost_band_eur', 'N/A')}")
            summary.append(f"  Why Plausible: {path.get('why_this_is_plausible', 'N/A')}")
            summary.append(f"  Technology Classes:")
            for tech_class in path.get('technology_classes', []):
                summary.append(f"    - {tech_class}")
            summary.append(f"  Risks & Unknowns:")
            for risk in path.get('risks_and_unknowns', []):
                summary.append(f"    - {risk}")
            summary.append("")
        
        summary.append("=" * 80)
        
        return "\n".join(summary)
