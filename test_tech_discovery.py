"""
Test suite for Technology Discovery Agent
"""

import json
import logging
from unittest.mock import Mock, MagicMock

from schemas import TECH_DISCOVERY_SCHEMA
from llm_client import OpenAIResponsesLLM
from tech_discovery_agent import TechnologyDiscoveryAgent
from database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_schema_validation():
    """Test that the JSON schema is valid"""
    logger.info("Testing JSON schema validation...")
    
    # Check schema structure
    assert TECH_DISCOVERY_SCHEMA['type'] == 'object'
    assert 'properties' in TECH_DISCOVERY_SCHEMA
    assert 'required' in TECH_DISCOVERY_SCHEMA
    
    # Check required fields
    required_fields = TECH_DISCOVERY_SCHEMA['required']
    assert 'challenge_summary' in required_fields
    assert 'core_functions' in required_fields
    assert 'underlying_principles' in required_fields
    assert 'technology_paths' in required_fields
    assert 'confidence' in required_fields
    
    # Check technology_paths structure
    tech_paths = TECH_DISCOVERY_SCHEMA['properties']['technology_paths']
    assert tech_paths['type'] == 'array'
    assert 'items' in tech_paths
    assert tech_paths['items']['type'] == 'object'
    
    logger.info("✓ Schema validation passed")
    return True


def test_mock_llm_client():
    """Test Technology Discovery Agent with mock LLM client"""
    logger.info("Testing Technology Discovery Agent with mock LLM...")
    
    # Create mock LLM client
    mock_llm = Mock()
    
    # Mock response that matches schema
    mock_response = {
        "challenge_summary": "Water scarcity in Sub-Saharan Africa",
        "core_functions": [
            "Collect water from atmosphere",
            "Store water safely",
            "Distribute water to users"
        ],
        "underlying_principles": [
            "Condensation of water vapor",
            "Gravity-driven flow",
            "Passive cooling"
        ],
        "technology_paths": [
            {
                "path_name": "Atmospheric Water Generation via Passive Condensation",
                "principles_used": ["Condensation of water vapor", "Passive cooling"],
                "technology_classes": [
                    "Dew collection panels",
                    "Fog nets",
                    "Condensation chambers"
                ],
                "why_this_is_plausible": "Passive condensation systems are widely used in arid regions and require no power",
                "estimated_cost_band_eur": "€500-€2000",
                "risks_and_unknowns": [
                    "Depends on local humidity levels",
                    "Requires regular cleaning",
                    "Limited daily water yield"
                ]
            },
            {
                "path_name": "Rainwater Harvesting with Low-Cost Storage",
                "principles_used": ["Gravity-driven flow"],
                "technology_classes": [
                    "Roof catchment systems",
                    "Ferrocement tanks",
                    "Sand filters"
                ],
                "why_this_is_plausible": "Proven technology with local materials and skills available",
                "estimated_cost_band_eur": "€1000-€5000",
                "risks_and_unknowns": [
                    "Depends on rainfall patterns",
                    "Tank sizing critical",
                    "Water quality management needed"
                ]
            }
        ],
        "confidence": 0.85
    }
    
    mock_llm.complete.return_value = json.dumps(mock_response)
    
    # Create agent
    agent = TechnologyDiscoveryAgent(llm_client=mock_llm, max_budget_eur=10000)
    
    # Test challenge
    test_challenge = {
        "challenge_id": 1,
        "challenge_title": "Water scarcity in Sub-Saharan Africa",
        "challenge_statement": "Over 500 million people lack access to clean water",
        "sdg_goals": [6, 13],
        "geography": "Sub-Saharan Africa",
        "target_groups": ["rural communities"],
        "sectors": ["water"]
    }
    
    # Run discovery
    result = agent.discover_technology_paths(test_challenge, model="gpt-4.1-mini")
    
    # Validate result
    assert result['challenge_summary'] == mock_response['challenge_summary']
    assert len(result['core_functions']) == 3
    assert len(result['underlying_principles']) == 3
    assert len(result['technology_paths']) == 2
    assert result['confidence'] == 0.85
    
    # Check metadata was added
    assert 'challenge_id' in result
    assert 'discovered_at' in result
    assert 'model_used' in result
    assert 'budget_constraint_eur' in result
    
    logger.info("✓ Mock LLM client test passed")
    return True


def test_prompt_generation():
    """Test prompt generation"""
    logger.info("Testing prompt generation...")
    
    # Create mock LLM client
    mock_llm = Mock()
    agent = TechnologyDiscoveryAgent(llm_client=mock_llm, max_budget_eur=10000)
    
    # Test challenge
    test_challenge = {
        "challenge_id": 1,
        "challenge_title": "Food waste composting",
        "challenge_statement": "Urban areas generate tons of organic waste daily",
        "sdg_goals": [11, 12],
        "geography": "Urban Europe",
        "target_groups": ["households", "restaurants"],
        "sectors": ["waste management"]
    }
    
    # Generate prompt
    prompt = agent.build_discovery_prompt(test_challenge)
    
    # Check prompt contains key elements
    assert "Food waste composting" in prompt
    assert "Urban areas generate tons of organic waste daily" in prompt
    assert "€10000" in prompt or "€10,000" in prompt
    assert "functions" in prompt.lower()
    assert "principles" in prompt.lower()
    assert "technology" in prompt.lower()
    
    logger.info("✓ Prompt generation test passed")
    return True


def test_budget_validation():
    """Test budget constraint validation"""
    logger.info("Testing budget constraint validation...")
    
    # Create mock LLM client
    mock_llm = Mock()
    agent = TechnologyDiscoveryAgent(llm_client=mock_llm, max_budget_eur=5000)
    
    # Mock response with path exceeding budget
    mock_response = {
        "challenge_summary": "Test challenge",
        "core_functions": ["Function 1"],
        "underlying_principles": ["Principle 1"],
        "technology_paths": [
            {
                "path_name": "Expensive Path",
                "principles_used": ["Principle 1"],
                "technology_classes": ["Tech Class 1"],
                "why_this_is_plausible": "It works",
                "estimated_cost_band_eur": "€3000-€8000",  # Exceeds €5000 budget
                "risks_and_unknowns": ["Risk 1"]
            }
        ],
        "confidence": 0.8
    }
    
    # Should log warning but not fail
    try:
        agent._validate_budget_constraint(mock_response)
        logger.info("✓ Budget validation test passed (warning logged)")
        return True
    except Exception as e:
        logger.error(f"✗ Budget validation test failed: {e}")
        return False


def test_database_schema():
    """Test that database schema can be loaded"""
    logger.info("Testing database schema...")
    
    try:
        # Read schema file
        with open('/home/ubuntu/sdg-challenge-pipeline/schema_tech_discovery.sql', 'r') as f:
            schema_sql = f.read()
        
        # Check for key tables
        assert 'CREATE TABLE' in schema_sql
        assert 'tech_discovery_run' in schema_sql
        assert 'tech_path' in schema_sql
        
        # Check for key columns
        assert 'challenge_id' in schema_sql
        assert 'technology_classes' in schema_sql
        assert 'budget_constraint_eur' in schema_sql
        
        logger.info("✓ Database schema test passed")
        return True
    except Exception as e:
        logger.error(f"✗ Database schema test failed: {e}")
        return False


def test_summary_formatting():
    """Test summary formatting"""
    logger.info("Testing summary formatting...")
    
    # Create mock LLM client
    mock_llm = Mock()
    agent = TechnologyDiscoveryAgent(llm_client=mock_llm, max_budget_eur=10000)
    
    # Test discovery result
    test_result = {
        "challenge_summary": "Test challenge",
        "core_functions": ["Function 1", "Function 2"],
        "underlying_principles": ["Principle 1", "Principle 2"],
        "technology_paths": [
            {
                "path_name": "Path 1",
                "principles_used": ["Principle 1"],
                "technology_classes": ["Tech Class 1", "Tech Class 2"],
                "why_this_is_plausible": "It's feasible",
                "estimated_cost_band_eur": "€1000-€3000",
                "risks_and_unknowns": ["Risk 1", "Risk 2"]
            }
        ],
        "confidence": 0.9
    }
    
    # Format summary
    summary = agent.format_discovery_summary(test_result)
    
    # Check summary contains key elements
    assert "TECHNOLOGY DISCOVERY RESULT" in summary
    assert "Test challenge" in summary
    assert "Function 1" in summary
    assert "Principle 1" in summary
    assert "Path 1" in summary
    assert "€1000-€3000" in summary
    assert "0.90" in summary
    
    logger.info("✓ Summary formatting test passed")
    return True


def main():
    """Run all tests"""
    logger.info("=" * 80)
    logger.info("Technology Discovery Agent - Test Suite")
    logger.info("=" * 80)
    
    tests = [
        ("Schema Validation", test_schema_validation),
        ("Mock LLM Client", test_mock_llm_client),
        ("Prompt Generation", test_prompt_generation),
        ("Budget Validation", test_budget_validation),
        ("Database Schema", test_database_schema),
        ("Summary Formatting", test_summary_formatting)
    ]
    
    results = {}
    
    for name, test_func in tests:
        logger.info("")
        logger.info(f"Running test: {name}")
        logger.info("-" * 80)
        try:
            results[name] = test_func()
        except Exception as e:
            logger.error(f"✗ Test {name} failed with exception: {e}")
            results[name] = False
    
    # Summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("Test Summary")
    logger.info("=" * 80)
    
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
