# Technology Discovery Agent

Complete guide to the Technology Discovery Agent - the second agent in the SDG Challenge → Technology Discovery pipeline.

---

## Overview

The **Technology Discovery Agent** takes challenge statements and discovers plausible technology pathways by reasoning from **problems → functions → principles → technology classes**.

### What It Does

✅ Maps challenges to technology classes (NOT products or brands)  
✅ Stays under €10,000 budget constraint  
✅ Uses existing, widely available technology  
✅ Generates 2-3 plausible paths per challenge  
✅ Provides cost bands and risk assessments  

### What It Does NOT Do

❌ Recommend specific products or brands  
❌ Optimize designs  
❌ Generate bills of materials  
❌ Promise technical feasibility  
❌ Replace engineering judgment  

---

## Architecture

```
Challenge Database
  ↓
Technology Discovery Agent
  ├─ Identify Core Functions
  ├─ Map to Principles
  ├─ Discover Technology Classes
  └─ Generate Plausible Paths
  ↓
Technology Paths Database
```

### Components

**1. LLM Client** (`llm_client.py`)
- OpenAI Responses API with Structured Outputs
- Guaranteed JSON shape (no parsing failures)
- JSON Schema validation enforced by API

**2. JSON Schema** (`schemas.py`)
- `TECH_DISCOVERY_SCHEMA`: Output structure definition
- Enforces required fields and data types
- Validates technology paths structure

**3. Technology Discovery Agent** (`tech_discovery_agent.py`)
- Core discovery logic
- Prompt engineering
- Budget constraint validation
- Summary formatting

**4. Database Schema** (`schema_tech_discovery.sql`)
- `tech_discovery_run`: Discovery run metadata
- `tech_path`: Individual technology paths

**5. Run Script** (`run_tech_discovery.py`)
- CLI for running discovery on challenges
- Batch processing support
- Database integration

---

## Installation

### 1. Initialize Database Schema

```bash
# Connect to your database (Supabase or local PostgreSQL)
psql "your_database_url"

# Load the technology discovery schema
\i schema_tech_discovery.sql

# Verify tables were created
\dt tech_*

# Exit
\q
```

### 2. Verify Dependencies

All required dependencies are already in `requirements.txt`:
- `openai>=2.0.0`
- `psycopg2-binary`
- `python-dotenv`

---

## Usage

### Quick Start

```bash
# Run discovery on a single challenge
python run_tech_discovery.py --challenge-id 123

# Run discovery on all challenges without paths (limit 10)
python run_tech_discovery.py --all --limit 10

# Use a specific model
python run_tech_discovery.py --challenge-id 123 --model gpt-4.1-mini

# Set custom budget constraint
python run_tech_discovery.py --challenge-id 123 --budget 5000
```

### Python API

```python
from database import Database
from llm_client import build_llm_client
from schemas import TECH_DISCOVERY_SCHEMA
from tech_discovery_agent import TechnologyDiscoveryAgent

# Initialize database
db = Database()
db.connect()

# Initialize LLM client with structured outputs
llm_client = build_llm_client(
    provider="openai_responses",
    schema=TECH_DISCOVERY_SCHEMA,
    schema_name="tech_discovery"
)

# Initialize Technology Discovery Agent
agent = TechnologyDiscoveryAgent(
    llm_client=llm_client,
    max_budget_eur=10000
)

# Get a challenge
challenges = db.execute(
    "SELECT * FROM challenge WHERE challenge_id = %s",
    (123,),
    fetch=True
)
challenge = dict(challenges[0])

# Run discovery
discovery_result = agent.discover_technology_paths(
    challenge,
    model="gpt-4.1-mini"
)

# Print summary
summary = agent.format_discovery_summary(discovery_result)
print(summary)

# Store in database
run_id = db.insert_tech_discovery_run(
    challenge_id=challenge['challenge_id'],
    model_used=discovery_result['model_used'],
    budget_constraint_eur=discovery_result['budget_constraint_eur'],
    challenge_summary=discovery_result['challenge_summary'],
    core_functions=discovery_result['core_functions'],
    underlying_principles=discovery_result['underlying_principles'],
    confidence=discovery_result['confidence'],
    full_response=discovery_result,
    status='completed'
)

# Store paths
for i, path in enumerate(discovery_result['technology_paths'], 1):
    db.insert_tech_path(
        run_id=run_id,
        challenge_id=challenge['challenge_id'],
        path_name=path['path_name'],
        path_order=i,
        principles_used=path['principles_used'],
        technology_classes=path['technology_classes'],
        why_plausible=path['why_this_is_plausible'],
        estimated_cost_band_eur=path['estimated_cost_band_eur'],
        risks_and_unknowns=path['risks_and_unknowns']
    )

db.disconnect()
```

---

## Output Structure

### Discovery Result

```json
{
  "challenge_summary": "Brief restatement of the challenge",
  "core_functions": [
    "Function 1: What must happen",
    "Function 2: Physical action required"
  ],
  "underlying_principles": [
    "Physical principle 1",
    "Chemical principle 2",
    "Mechanical principle 3"
  ],
  "technology_paths": [
    {
      "path_name": "Descriptive name for this path",
      "principles_used": ["Principle 1", "Principle 2"],
      "technology_classes": [
        "Technology class 1 (NOT a brand)",
        "Technology class 2"
      ],
      "why_this_is_plausible": "Explanation of feasibility",
      "estimated_cost_band_eur": "€500-€2000",
      "risks_and_unknowns": [
        "Risk 1",
        "Unknown 2"
      ]
    }
  ],
  "confidence": 0.85,
  "challenge_id": 123,
  "discovered_at": "2026-01-11T12:00:00",
  "model_used": "gpt-4.1-mini",
  "budget_constraint_eur": 10000
}
```

---

## Example Discovery

### Input Challenge

```
Title: Water scarcity in Sub-Saharan Africa
Statement: Over 500 million people in Sub-Saharan Africa lack access to clean water due to inadequate infrastructure and limited funding.
SDG Goals: 6, 13
Geography: Sub-Saharan Africa
Target Groups: Rural communities
Sectors: Water
```

### Output (Simplified)

```
TECHNOLOGY DISCOVERY RESULT
================================================================================

Challenge: Water scarcity affecting 500M people in Sub-Saharan Africa
Confidence: 0.85
Budget Constraint: €10000

CORE FUNCTIONS:
  • Collect water from atmosphere or surface
  • Store water safely
  • Distribute water to users
  • Purify contaminated water

UNDERLYING PRINCIPLES:
  • Condensation of water vapor
  • Gravity-driven flow
  • Passive cooling
  • Filtration and sedimentation

TECHNOLOGY PATHS (2 discovered):

Path 1: Atmospheric Water Generation via Passive Condensation
  Cost Band: €500-€2000
  Why Plausible: Passive condensation systems are widely used in arid regions
  Technology Classes:
    - Dew collection panels
    - Fog nets
    - Condensation chambers
  Risks & Unknowns:
    - Depends on local humidity levels
    - Requires regular cleaning
    - Limited daily water yield

Path 2: Rainwater Harvesting with Low-Cost Storage
  Cost Band: €1000-€5000
  Why Plausible: Proven technology with local materials available
  Technology Classes:
    - Roof catchment systems
    - Ferrocement tanks
    - Sand filters
  Risks & Unknowns:
    - Depends on rainfall patterns
    - Tank sizing critical
    - Water quality management needed
```

---

## Database Schema

### tech_discovery_run

| Column | Type | Description |
|--------|------|-------------|
| `run_id` | SERIAL | Primary key |
| `challenge_id` | INTEGER | Reference to challenge |
| `discovered_at` | TIMESTAMP | When discovery was run |
| `model_used` | VARCHAR(100) | LLM model used |
| `budget_constraint_eur` | INTEGER | Budget constraint (default: 10000) |
| `challenge_summary` | TEXT | Brief challenge restatement |
| `core_functions` | JSONB | Array of function strings |
| `underlying_principles` | JSONB | Array of principle strings |
| `confidence` | DECIMAL(3,2) | Confidence score (0-1) |
| `full_response` | JSONB | Complete LLM response |
| `status` | VARCHAR(50) | completed, failed, in_progress |
| `error_message` | TEXT | Error if failed |

### tech_path

| Column | Type | Description |
|--------|------|-------------|
| `path_id` | SERIAL | Primary key |
| `run_id` | INTEGER | Reference to discovery run |
| `challenge_id` | INTEGER | Reference to challenge |
| `path_name` | VARCHAR(500) | Descriptive path name |
| `path_order` | INTEGER | Order in result (1, 2, 3) |
| `principles_used` | JSONB | Array of principle strings |
| `technology_classes` | JSONB | Array of technology class strings |
| `why_plausible` | TEXT | Feasibility explanation |
| `estimated_cost_band_eur` | VARCHAR(100) | Cost range (e.g., "€500-€2000") |
| `risks_and_unknowns` | JSONB | Array of risk strings |

---

## Querying Results

### Get All Discovery Runs

```sql
SELECT 
  run_id,
  challenge_id,
  challenge_summary,
  confidence,
  discovered_at
FROM tech_discovery_run
ORDER BY discovered_at DESC
LIMIT 10;
```

### Get Technology Paths for a Challenge

```sql
SELECT 
  tp.path_name,
  tp.estimated_cost_band_eur,
  tp.technology_classes,
  tdr.confidence
FROM tech_path tp
JOIN tech_discovery_run tdr ON tp.run_id = tdr.run_id
WHERE tp.challenge_id = 123
ORDER BY tp.path_order;
```

### Get Challenges with Paths

```sql
SELECT 
  c.challenge_id,
  c.challenge_title,
  COUNT(tp.path_id) as num_paths,
  MAX(tdr.discovered_at) as last_discovery
FROM challenge c
LEFT JOIN tech_discovery_run tdr ON c.challenge_id = tdr.challenge_id
LEFT JOIN tech_path tp ON tdr.run_id = tp.run_id
GROUP BY c.challenge_id, c.challenge_title
HAVING COUNT(tp.path_id) > 0
ORDER BY last_discovery DESC;
```

---

## Testing

```bash
# Run test suite
python test_tech_discovery.py
```

**Tests included:**
- ✓ Schema Validation
- ✓ Mock LLM Client
- ✓ Prompt Generation
- ✓ Budget Validation
- ✓ Database Schema
- ✓ Summary Formatting

---

## Configuration

### Environment Variables

```env
# LLM Configuration
OPENAI_API_KEY=your_api_key_here
LLM_MODEL=gpt-4.1-mini

# Database Configuration
DATABASE_URL=postgresql://...
```

### Budget Constraint

Default: €10,000

Change via:
- Command line: `--budget 5000`
- Python API: `TechnologyDiscoveryAgent(llm_client, max_budget_eur=5000)`

---

## Prompt Engineering

### System Prompt

```
You are a constraint-driven technology discovery agent specializing in 
finding feasible technology pathways for sustainability challenges.

Your approach:
1. Start with the problem, not the solution
2. Reason from functions → principles → technology classes
3. Stay under €10,000 budget constraint
4. Use existing, widely available technology
5. Never recommend specific brands or products
6. Focus on human-scale, locally feasible solutions
```

### User Prompt Structure

1. **Challenge Context**: Title, statement, SDG goals, geography
2. **Task Definition**: Identify functions, map to principles, discover paths
3. **Constraints**: Budget, no brands, existing technology, human-scale
4. **Output Requirements**: 2-3 paths, cost bands, risks

---

## Best Practices

### For Users

1. **Start with good challenges**: Use Challenge Extractor Agent first
2. **Review multiple paths**: Agent provides options, not answers
3. **Validate locally**: Check if technology is available in target geography
4. **Iterate**: Adjust budget or constraints and re-run if needed
5. **Human review**: Always validate with domain experts

### For Developers

1. **Structured outputs**: Always use JSON Schema validation
2. **Budget validation**: Log warnings but don't fail on minor overages
3. **Error handling**: Store failed runs in database for debugging
4. **Prompt tuning**: Test with diverse challenges and iterate
5. **Batch processing**: Use `--all` for processing multiple challenges

---

## Troubleshooting

### Issue: No technology paths generated

**Possible causes:**
- Challenge is too vague or solution-heavy
- Budget constraint is too restrictive
- LLM model doesn't support structured outputs

**Solution:**
- Refine challenge statement
- Increase budget constraint
- Check model compatibility

### Issue: Paths exceed budget

**Solution:**
- Agent logs warnings but doesn't fail
- Review paths and adjust budget if needed
- LLM may have good reasons for exceeding budget slightly

### Issue: Database connection error

**Solution:**
```bash
# Verify database URL
echo $DATABASE_URL

# Test connection
psql "$DATABASE_URL" -c "SELECT 1"

# Reload schema if needed
psql "$DATABASE_URL" -f schema_tech_discovery.sql
```

---

## Roadmap

### Phase 2 Enhancements

- [ ] **Technology signal injection**: Add real-world technology signals to prompts
- [ ] **Cost estimation API**: Integrate with pricing databases
- [ ] **Human-in-the-loop**: Add review and refinement workflow
- [ ] **Path comparison**: Score and rank paths by feasibility
- [ ] **Local availability check**: Validate technology availability by geography
- [ ] **Multi-model support**: Test with different LLMs
- [ ] **Prompt library**: Store and version prompts in database

---

## Support

- **GitHub Issues**: https://github.com/Lennart1970/sdg-challenge-pipeline/issues
- **Documentation**: See [README.md](README.md)
- **Quick Start**: See [QUICKSTART.md](QUICKSTART.md)

---

**Discover, don't invent. Reality beats novelty.**
