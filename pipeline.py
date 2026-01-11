"""
Main orchestration script for the SDG Challenge Extraction Pipeline
"""

import json
import logging
import sys
from typing import List, Dict
from database import Database
from crawler import Crawler
from chunker import TextChunker
from extractor import ChallengeExtractor
from deduplicator import Deduplicator
from scorer import ChallengeScorer
from config import LOG_LEVEL, LOG_FILE, BATCH_SIZE, MIN_CONFIDENCE, MIN_OVERALL_SCORE, MAX_SOLUTION_LEAKAGE

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SDGPipeline:
    """Main pipeline orchestrator"""
    
    def __init__(self):
        self.db = Database()
        self.crawler = Crawler()
        self.chunker = TextChunker()
        self.extractor = ChallengeExtractor()
        self.deduplicator = Deduplicator()
        self.scorer = ChallengeScorer()
        
    def run(self):
        """Run the complete pipeline"""
        try:
            logger.info("Starting SDG Challenge Extraction Pipeline")
            
            # Phase 1: Connect to database
            logger.info("Phase 1: Connecting to database...")
            self.db.connect()
            
            # Phase 2: Seed data (if needed)
            logger.info("Phase 2: Seeding organizations and feeds...")
            self._seed_data()
            
            # Phase 3: Discover and fetch documents
            logger.info("Phase 3: Discovering and fetching documents...")
            self._discover_and_fetch()
            
            # Phase 4: Extract challenges
            logger.info("Phase 4: Extracting challenges...")
            self._extract_challenges()
            
            # Phase 5: Deduplicate
            logger.info("Phase 5: Deduplicating challenges...")
            self._deduplicate_challenges()
            
            # Phase 6: Score challenges
            logger.info("Phase 6: Scoring challenges...")
            self._score_challenges()
            
            logger.info("Pipeline completed successfully")
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            sys.exit(1)
        finally:
            self.db.disconnect()
            
    def _seed_data(self):
        """Seed organizations and source feeds"""
        try:
            self.db.seed_organizations()
            logger.info("Data seeded successfully")
        except Exception as e:
            logger.warning(f"Seeding failed (may already exist): {e}")
            
    def _discover_and_fetch(self):
        """Discover URLs and fetch documents"""
        # Get all active feeds
        feeds = self.db.execute(
            "SELECT feed_id, base_url, org_id FROM source_feed WHERE active = TRUE",
            fetch=True
        )
        
        logger.info(f"Found {len(feeds)} active feeds")
        
        for feed in feeds:
            feed_id = feed['feed_id']
            base_url = feed['base_url']
            org_id = feed['org_id']
            
            logger.info(f"Processing feed {feed_id}: {base_url}")
            
            try:
                # Discover URLs (simple crawl, depth=1 for MVP)
                discovered_urls = self.crawler.discover_urls(base_url, max_depth=1)
                logger.info(f"Discovered {len(discovered_urls)} URLs")
                
                # Fetch each URL
                for url in discovered_urls[:10]:  # Limit to 10 per feed for MVP
                    try:
                        result = self.crawler.fetch_url(url)
                        if result and 'error' not in result:
                            # Insert into database
                            self.db.insert_raw_document(feed_id, **result)
                            logger.info(f"Fetched and stored: {url}")
                        else:
                            logger.warning(f"Failed to fetch: {url}")
                    except Exception as e:
                        logger.error(f"Error fetching {url}: {e}")
                        
            except Exception as e:
                logger.error(f"Error processing feed {feed_id}: {e}")
                
    def _extract_challenges(self):
        """Extract challenges from fetched documents"""
        # Get unprocessed documents
        documents = self.db.get_unprocessed_documents('extraction', limit=BATCH_SIZE)
        
        logger.info(f"Found {len(documents)} documents to process")
        
        for doc in documents:
            doc_id = doc['doc_id']
            text_content = doc['text_content']
            org_id = doc['org_id']
            org_name = doc['org_name']
            url = doc['url']
            
            try:
                # Chunk the document
                chunks = self.chunker.chunk_document(text_content, {"doc_id": doc_id})
                
                if not chunks:
                    self.db.mark_processing_state(doc_id, 'extraction', 'skipped', 'No chunks')
                    continue
                
                # Extract challenges from chunks
                all_challenges = self.extractor.extract_batch(chunks, org_name, url)
                
                if not all_challenges:
                    self.db.mark_processing_state(doc_id, 'extraction', 'completed', None)
                    continue
                
                # Add fingerprints
                all_challenges = self.deduplicator.add_fingerprints(all_challenges)
                
                # Insert challenges into database
                for challenge in all_challenges:
                    try:
                        self.db.insert_challenge(
                            doc_id,
                            org_id,
                            challenge_title=challenge.get('challenge_title'),
                            challenge_statement=challenge['challenge_statement'],
                            sdg_goals=challenge.get('sdg_goals', []),
                            geography=challenge.get('geography'),
                            target_groups=challenge.get('target_groups', []),
                            sectors=challenge.get('sectors', []),
                            scale_numbers=challenge.get('scale_numbers', {}),
                            root_causes=challenge.get('root_causes', []),
                            constraints=challenge.get('constraints', []),
                            evidence_quotes=challenge.get('evidence_quotes', []),
                            confidence=challenge.get('confidence', 0.70),
                            extraction_model='gpt-4.1-mini',
                            statement_fingerprint=challenge.get('statement_fingerprint')
                        )
                    except Exception as e:
                        logger.error(f"Error inserting challenge: {e}")
                
                self.db.mark_processing_state(doc_id, 'extraction', 'completed', None)
                logger.info(f"Extracted {len(all_challenges)} challenges from doc {doc_id}")
                
            except Exception as e:
                logger.error(f"Error extracting from doc {doc_id}: {e}")
                self.db.mark_processing_state(doc_id, 'extraction', 'failed', str(e))
                
    def _deduplicate_challenges(self):
        """Find and merge duplicate challenges"""
        try:
            # Get all challenges
            all_challenges = self.db.get_all_challenges()
            logger.info(f"Deduplicating {len(all_challenges)} challenges")
            
            # Find duplicates
            duplicate_groups = self.deduplicator.find_duplicates(all_challenges)
            logger.info(f"Found {len(duplicate_groups)} duplicate groups")
            
            # Merge duplicates
            if duplicate_groups:
                merged = self.deduplicator.merge_duplicates(all_challenges, duplicate_groups)
                
                # Delete duplicates from database
                for group in duplicate_groups:
                    for idx in group[1:]:  # Keep first, delete rest
                        if idx < len(all_challenges):
                            challenge_id = all_challenges[idx]['challenge_id']
                            self.db.delete_challenge(challenge_id)
                            
        except Exception as e:
            logger.error(f"Error deduplicating: {e}")
            
    def _score_challenges(self):
        """Score all challenges"""
        try:
            # Get all challenges
            all_challenges = self.db.get_all_challenges()
            logger.info(f"Scoring {len(all_challenges)} challenges")
            
            # Score each challenge
            for challenge in all_challenges:
                try:
                    score = self.scorer.score_challenge(challenge)
                    self.db.insert_challenge_score(challenge['challenge_id'], **score)
                except Exception as e:
                    logger.error(f"Error scoring challenge {challenge['challenge_id']}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in scoring phase: {e}")


def main():
    """Main entry point"""
    pipeline = SDGPipeline()
    pipeline.run()


if __name__ == "__main__":
    main()
