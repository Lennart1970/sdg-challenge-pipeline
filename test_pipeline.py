"""
Test script for validating the SDG Challenge Extraction Pipeline
"""

import logging
from database import Database
from chunker import TextChunker
from extractor import ChallengeExtractor
from deduplicator import Deduplicator
from scorer import ChallengeScorer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_database():
    """Test database connection and seeding"""
    logger.info("Testing database connection...")
    db = Database()
    db.connect()
    
    # Seed data
    logger.info("Seeding organizations and feeds...")
    try:
        db.seed_organizations()
        logger.info("✓ Seeding successful")
    except Exception as e:
        logger.warning(f"Seeding warning (may already exist): {e}")
    
    # Check organizations
    orgs = db.execute("SELECT COUNT(*) as count FROM org", fetch=True)
    logger.info(f"✓ Organizations in database: {orgs[0]['count']}")
    
    # Check feeds
    feeds = db.execute("SELECT COUNT(*) as count FROM source_feed", fetch=True)
    logger.info(f"✓ Source feeds in database: {feeds[0]['count']}")
    
    db.disconnect()
    return True


def test_chunker():
    """Test text chunking"""
    logger.info("Testing text chunker...")
    
    sample_text = """
    Water Scarcity in Sub-Saharan Africa
    
    Over 500 million people in Sub-Saharan Africa lack access to clean water.
    This is due to inadequate infrastructure, climate change impacts, and limited funding.
    
    The problem is particularly acute in rural areas where communities rely on 
    contaminated water sources, leading to waterborne diseases.
    
    Key barriers include:
    - Insufficient water treatment facilities
    - Lack of maintenance capacity
    - Limited government budgets
    - Poor coordination between stakeholders
    """
    
    chunker = TextChunker(chunk_size=50, overlap=0.15)
    chunks = chunker.chunk_document(sample_text)
    
    logger.info(f"✓ Created {len(chunks)} chunks from sample text")
    for i, chunk in enumerate(chunks):
        logger.info(f"  Chunk {i+1}: {len(chunk['text'].split())} words")
    
    return True


def test_extractor():
    """Test LLM extraction (with sample text)"""
    logger.info("Testing challenge extractor...")
    
    sample_chunk = """
    Water scarcity affects over 500 million people in Sub-Saharan Africa, 
    with inadequate infrastructure and limited funding creating barriers to access. 
    Rural communities face particular challenges with contaminated water sources 
    leading to waterborne diseases.
    """
    
    extractor = ChallengeExtractor()
    
    try:
        challenges = extractor.extract_challenges(
            sample_chunk,
            "World Bank",
            "https://example.com/test"
        )
        
        logger.info(f"✓ Extracted {len(challenges)} challenges")
        for i, challenge in enumerate(challenges):
            logger.info(f"  Challenge {i+1}: {challenge.get('challenge_title', 'N/A')}")
            logger.info(f"    Statement: {challenge.get('challenge_statement', '')[:100]}...")
            logger.info(f"    Confidence: {challenge.get('confidence', 0)}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Extraction failed: {e}")
        return False


def test_deduplicator():
    """Test deduplication"""
    logger.info("Testing deduplicator...")
    
    sample_challenges = [
        {"challenge_statement": "Water scarcity affects 500 million people in Africa"},
        {"challenge_statement": "Water scarcity impacts 500M people across Africa"},
        {"challenge_statement": "Food insecurity is a major challenge in rural areas"}
    ]
    
    dedup = Deduplicator()
    
    # Add fingerprints
    challenges_with_fp = dedup.add_fingerprints(sample_challenges)
    logger.info(f"✓ Added fingerprints to {len(challenges_with_fp)} challenges")
    
    # Find duplicates
    duplicate_groups = dedup.find_duplicates(challenges_with_fp)
    logger.info(f"✓ Found {len(duplicate_groups)} duplicate groups")
    
    return True


def test_scorer():
    """Test scoring"""
    logger.info("Testing scorer...")
    
    sample_challenge = {
        "challenge_statement": "Water scarcity affects 500 million people in Sub-Saharan Africa due to inadequate infrastructure and limited funding",
        "sdg_goals": [6, 13],
        "geography": "Sub-Saharan Africa",
        "target_groups": ["rural communities"],
        "sectors": ["water"],
        "scale_numbers": {"people_affected": 500000000},
        "root_causes": ["inadequate infrastructure", "limited funding"],
        "constraints": ["funding", "infrastructure"],
        "evidence_quotes": ["500 million people lack access"],
        "confidence": 0.85
    }
    
    scorer = ChallengeScorer()
    score = scorer.score_challenge(sample_challenge)
    
    logger.info(f"✓ Scored challenge:")
    logger.info(f"  Challenge density: {score['challenge_density']}")
    logger.info(f"  Solution leakage: {score['solution_leakage']}")
    logger.info(f"  Specificity: {score['specificity']}")
    logger.info(f"  Evidence strength: {score['evidence_strength']}")
    logger.info(f"  Overall score: {score['overall_score']}")
    
    return True


def main():
    """Run all tests"""
    logger.info("=" * 60)
    logger.info("SDG Challenge Extraction Pipeline - Test Suite")
    logger.info("=" * 60)
    
    tests = [
        ("Database", test_database),
        ("Chunker", test_chunker),
        ("Extractor", test_extractor),
        ("Deduplicator", test_deduplicator),
        ("Scorer", test_scorer)
    ]
    
    results = {}
    
    for name, test_func in tests:
        logger.info("")
        logger.info(f"Running test: {name}")
        logger.info("-" * 60)
        try:
            results[name] = test_func()
        except Exception as e:
            logger.error(f"✗ Test {name} failed with exception: {e}")
            results[name] = False
    
    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("Test Summary")
    logger.info("=" * 60)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {name}")
    
    logger.info("")
    logger.info(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("✓ All tests passed!")
        return 0
    else:
        logger.error("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    exit(main())
