#!/usr/bin/env python3
"""
Run Technology Discovery on Challenges

This script takes challenge IDs and runs the Technology Discovery Agent
to generate plausible technology paths under budget constraint.

Usage:
    python run_tech_discovery.py --challenge-id 123
    python run_tech_discovery.py --challenge-id 123 --model gpt-4.1-mini
    python run_tech_discovery.py --all --limit 10
"""

import argparse
import logging
import sys
from typing import Optional

from database import Database
from llm_client import build_llm_client
from schemas import TECH_DISCOVERY_SCHEMA
from tech_discovery_agent import TechnologyDiscoveryAgent
from config import LLM_MODEL

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_discovery_for_challenge(
    db: Database,
    agent: TechnologyDiscoveryAgent,
    challenge_id: int,
    model: str
) -> Optional[int]:
    """
    Run technology discovery for a single challenge
    
    Args:
        db: Database connection
        agent: Technology Discovery Agent
        challenge_id: Challenge ID
        model: LLM model to use
        
    Returns:
        run_id if successful, None otherwise
    """
    try:
        # Get challenge from database
        logger.info(f"Fetching challenge {challenge_id}...")
        challenges = db.execute(
            "SELECT * FROM challenge WHERE challenge_id = %s",
            (challenge_id,),
            fetch=True
        )
        
        if not challenges:
            logger.error(f"Challenge {challenge_id} not found")
            return None
        
        challenge = dict(challenges[0])
        logger.info(f"Challenge: {challenge.get('challenge_title', 'Untitled')}")
        
        # Run technology discovery
        logger.info("Running technology discovery...")
        discovery_result = agent.discover_technology_paths(challenge, model=model)
        
        # Print summary
        summary = agent.format_discovery_summary(discovery_result)
        print("\n" + summary + "\n")
        
        # Store in database
        logger.info("Storing results in database...")
        
        # Insert discovery run
        run_id = db.insert_tech_discovery_run(
            challenge_id=challenge_id,
            model_used=discovery_result.get('model_used', model),
            budget_constraint_eur=discovery_result.get('budget_constraint_eur', 10000),
            challenge_summary=discovery_result.get('challenge_summary', ''),
            core_functions=discovery_result.get('core_functions', []),
            underlying_principles=discovery_result.get('underlying_principles', []),
            confidence=discovery_result.get('confidence', 0.0),
            full_response=discovery_result,
            status='completed'
        )
        
        # Insert technology paths
        paths = discovery_result.get('technology_paths', [])
        for i, path in enumerate(paths, 1):
            db.insert_tech_path(
                run_id=run_id,
                challenge_id=challenge_id,
                path_name=path.get('path_name', f'Path {i}'),
                path_order=i,
                principles_used=path.get('principles_used', []),
                technology_classes=path.get('technology_classes', []),
                why_plausible=path.get('why_this_is_plausible', ''),
                estimated_cost_band_eur=path.get('estimated_cost_band_eur', ''),
                risks_and_unknowns=path.get('risks_and_unknowns', [])
            )
        
        logger.info(f"✓ Successfully completed discovery run {run_id} with {len(paths)} paths")
        return run_id
        
    except Exception as e:
        logger.error(f"Error during technology discovery: {e}", exc_info=True)
        
        # Try to record failure in database
        try:
            run_id = db.insert_tech_discovery_run(
                challenge_id=challenge_id,
                model_used=model,
                budget_constraint_eur=10000,
                challenge_summary='',
                core_functions=[],
                underlying_principles=[],
                confidence=0.0,
                full_response={},
                status='failed',
                error_message=str(e)
            )
            logger.info(f"Recorded failed run {run_id}")
        except Exception as db_error:
            logger.error(f"Could not record failure: {db_error}")
        
        return None


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Run Technology Discovery Agent on challenges'
    )
    
    parser.add_argument(
        '--challenge-id',
        type=int,
        help='Challenge ID to process'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Process all challenges without technology paths'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Maximum number of challenges to process (with --all)'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        default=LLM_MODEL,
        help=f'LLM model to use (default: {LLM_MODEL})'
    )
    
    parser.add_argument(
        '--budget',
        type=int,
        default=10000,
        help='Budget constraint in euros (default: 10000)'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.challenge_id and not args.all:
        parser.error("Either --challenge-id or --all must be specified")
    
    if args.challenge_id and args.all:
        parser.error("Cannot specify both --challenge-id and --all")
    
    # Initialize database
    logger.info("Connecting to database...")
    db = Database()
    db.connect()
    
    # Initialize LLM client with structured outputs
    logger.info(f"Initializing LLM client with model: {args.model}")
    llm_client = build_llm_client(
        provider="openai_responses",
        schema=TECH_DISCOVERY_SCHEMA,
        schema_name="tech_discovery"
    )
    
    # Initialize Technology Discovery Agent
    logger.info(f"Initializing Technology Discovery Agent with budget: €{args.budget}")
    agent = TechnologyDiscoveryAgent(
        llm_client=llm_client,
        max_budget_eur=args.budget
    )
    
    # Process challenges
    if args.challenge_id:
        # Single challenge
        run_id = run_discovery_for_challenge(
            db=db,
            agent=agent,
            challenge_id=args.challenge_id,
            model=args.model
        )
        
        if run_id:
            print(f"\n✓ Discovery run completed: {run_id}")
            sys.exit(0)
        else:
            print(f"\n✗ Discovery run failed")
            sys.exit(1)
    
    else:
        # All challenges without paths
        logger.info(f"Finding challenges without technology paths (limit: {args.limit})...")
        
        # Get challenges that don't have discovery runs yet
        query = """
            SELECT c.challenge_id, c.challenge_title
            FROM challenge c
            LEFT JOIN tech_discovery_run tdr ON c.challenge_id = tdr.challenge_id
            WHERE tdr.run_id IS NULL
            ORDER BY c.extracted_at DESC
            LIMIT %s
        """
        
        challenges = db.execute(query, (args.limit,), fetch=True)
        
        if not challenges:
            logger.info("No challenges found without technology paths")
            db.disconnect()
            sys.exit(0)
        
        logger.info(f"Found {len(challenges)} challenges to process")
        
        # Process each challenge
        success_count = 0
        fail_count = 0
        
        for i, challenge in enumerate(challenges, 1):
            challenge_id = challenge['challenge_id']
            challenge_title = challenge['challenge_title']
            
            logger.info(f"\n[{i}/{len(challenges)}] Processing challenge {challenge_id}: {challenge_title}")
            
            run_id = run_discovery_for_challenge(
                db=db,
                agent=agent,
                challenge_id=challenge_id,
                model=args.model
            )
            
            if run_id:
                success_count += 1
            else:
                fail_count += 1
        
        # Summary
        print("\n" + "=" * 80)
        print("BATCH PROCESSING SUMMARY")
        print("=" * 80)
        print(f"Total challenges: {len(challenges)}")
        print(f"Successful: {success_count}")
        print(f"Failed: {fail_count}")
        print("=" * 80)
    
    # Cleanup
    db.disconnect()
    logger.info("Done")


if __name__ == "__main__":
    main()
