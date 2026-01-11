# SDG Challenge Extraction Pipeline

A comprehensive, production-ready MVP for extracting and analyzing Sustainable Development Goal (SDG) challenges from diverse sources including UN registries, multilateral development banks, EU research databases, government portals, and corporate ESG reports.

## Overview

This pipeline automates the discovery, extraction, deduplication, and scoring of SDG-related challenges from structured and unstructured sources. It uses LLM-based extraction to identify problem statements while filtering out solution language, ensuring focus on actual challenges rather than proposed interventions.

### Key Features

- **Multi-source discovery**: Crawls UN SDG registries, World Bank projects, EU CORDIS, government portals, and corporate reports
- **LLM-powered extraction**: Uses OpenAI GPT-4 to extract challenge statements with high precision
- **Intelligent deduplication**: Fingerprinting and merging of duplicate challenges
- **Quality scoring**: Multi-dimensional scoring (challenge density, specificity, evidence, recency)
- **PostgreSQL backend**: Scalable relational database with full referential integrity
- **Batch processing**: State tracking for reliable, resumable processing
- **Multilingual support**: Handles English and Dutch content

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SDG Challenge Pipeline                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. DISCOVERY & FETCH          2. EXTRACTION                 │
│  ├─ Crawler                    ├─ Chunker                    │
│  ├─ URL harvesting             ├─ LLM Extractor             │
│  └─ Document storage           └─ Metadata parsing          │
│                                                               │
│  3. DEDUPLICATION              4. SCORING                    │
│  ├─ Fingerprinting             ├─ Challenge density         │
│  ├─ Duplicate detection        ├─ Specificity               │
│  └─ Evidence merging           ├─ Evidence strength         │
│                                └─ Quality filtering         │
│                                                               │
│                    PostgreSQL Database                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ org | source_feed | raw_document | challenge |       │   │
│  │ initiative | initiative_challenge | challenge_score  │   │
│  │ processing_state                                     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- OpenAI API key

### Setup

1. **Clone or download the repository**:
   ```bash
   cd sdg-challenge-pipeline
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials and OpenAI API key
   ```

4. **Initialize PostgreSQL database**:
   ```bash
   sudo -u postgres psql -d sdg_challenges -f schema.sql
   ```

## Quick Start

### 1. Seed Organizations and Feeds

The pipeline comes with a pre-configured seed list of 18 organizations and 18 source feeds:

**Organizations**:
- UN (5 entities): SDG Platform, Sustainable Development, UNSDG, Local2030, Global Compact
- Multilateral Development Banks (4): World Bank, AfDB, ADB, EIB
- EU (2): CORDIS, Commission Policies
- National/Local Government (4): Netherlands, CBS, Amsterdam, Noord-Holland
- Corporate & NGO (3): Coca-Cola, Oxfam, WRI

**Source Feeds**: 18 feeds covering registries, portals, and PDF indexes

### 2. Run the Pipeline

```bash
python pipeline.py
```

This will:
1. Connect to PostgreSQL
2. Seed organizations and feeds
3. Discover and fetch documents from active feeds
4. Extract challenges using LLM
5. Deduplicate challenges
6. Score all challenges

### 3. Query Results

```python
from database import Database

db = Database()
db.connect()

# Get all challenges
challenges = db.get_all_challenges(limit=10)
for c in challenges:
    print(f"Title: {c['challenge_title']}")
    print(f"Statement: {c['challenge_statement']}")
    print(f"Confidence: {c['confidence']}")
    print()

db.disconnect()
```

## Configuration

### Database

Edit `.env` to configure PostgreSQL connection:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sdg_challenges
DB_USER=postgres
DB_PASSWORD=your_password
```

### LLM

Configure OpenAI API:

```env
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4.1-mini
LLM_TEMPERATURE=0.3
```

### Crawler

Adjust crawling behavior:

```env
CRAWLER_TIMEOUT=30
CRAWLER_MAX_RETRIES=3
CHUNK_SIZE=1000
CHUNK_OVERLAP=0.15
```

## Database Schema

### Core Tables

| Table | Purpose |
|-------|---------|
| `org` | Organizations (UN, MDB, EU, governments, corporates, NGOs) |
| `source_feed` | Data sources (registries, portals, PDF indexes) |
| `raw_document` | Fetched pages/PDFs with extracted text |
| `challenge` | Extracted challenge statements |
| `initiative` | Projects/programs metadata (optional) |
| `challenge_score` | Quality scores for each challenge |
| `processing_state` | Batch processing state tracking |

### Key Indexes

- `raw_document_url_uq`: Unique URL constraint
- `raw_document_hash_idx`: Deduplication by content hash
- `challenge_fingerprint_idx`: Deduplication by statement fingerprint
- `processing_state_stage_idx`: Batch processing queries

## Pipeline Phases

### Phase 1: Discovery & Fetch
- Crawls source feeds (registries, portals)
- Discovers URLs matching project/initiative patterns
- Fetches HTML/PDF content
- Extracts clean text

### Phase 2: Chunking
- Splits documents into meaningful chunks (800-1200 tokens)
- Preserves section structure
- Implements 15% overlap for context

### Phase 3: LLM Extraction
- Sends chunks to OpenAI GPT-4
- Extracts challenge statements (1-2 sentences, no solutions)
- Captures metadata: SDG goals, geography, target groups, sectors, constraints

### Phase 4: Deduplication
- Creates normalized fingerprints of challenge statements
- Identifies duplicate challenges
- Merges duplicates, combining evidence

### Phase 5: Scoring
- **Challenge Density** (35%): Frequency of challenge keywords
- **Specificity** (25%): Presence of numbers, geography, target groups
- **Evidence Strength** (20%): Quotes, root causes, constraints
- **Recency** (10%): Document freshness
- **Solution Leakage** (-20%): Penalizes solution language

### Phase 6: Filtering
- Removes challenges with:
  - Overall score < 40
  - Confidence < 0.50
  - Solution leakage > 70

## Keyword Reference

### Challenge Signals (Positive)

**English**: barrier, constraint, bottleneck, gap, unmet need, risk, vulnerability, inequality, shortage, lack of, needs assessment, baseline, problem statement, context, rationale

**Dutch**: uitdaging, knelpunt, belemmering, tekort, kwetsbaarheid, achterstand

### Solution Leakage (Negative)

**English**: implement, develop, deploy, rollout, build, deliver, pilot, prototype, intervention

**Dutch**: implementeren, ontwikkelen, uitrollen, pilot

## API Reference

### Database Operations

```python
from database import Database

db = Database()
db.connect()

# Insert raw document
doc_id = db.insert_raw_document(
    feed_id=1,
    url="https://example.com/project",
    text_content="...",
    title="Project Name",
    http_status=200
)

# Insert challenge
challenge_id = db.insert_challenge(
    doc_id=doc_id,
    org_id=1,
    challenge_statement="Water scarcity affects 500M people in Sub-Saharan Africa",
    sdg_goals=[6, 13],
    geography="Sub-Saharan Africa",
    confidence=0.85
)

# Score challenge
db.insert_challenge_score(
    challenge_id=challenge_id,
    challenge_density=75,
    overall_score=68,
    scoring_notes="High density, good specificity"
)

db.disconnect()
```

### Extraction

```python
from extractor import ChallengeExtractor
from chunker import TextChunker

chunker = TextChunker()
extractor = ChallengeExtractor()

# Chunk text
chunks = chunker.chunk_document(text_content)

# Extract challenges
challenges = extractor.extract_batch(
    chunks,
    org_name="World Bank",
    url="https://projects.worldbank.org/..."
)
```

### Scoring

```python
from scorer import ChallengeScorer

scorer = ChallengeScorer()

# Score single challenge
score = scorer.score_challenge(challenge)

# Score batch
scored = scorer.score_batch(challenges)

# Filter by quality
filtered = scorer.filter_challenges(
    challenges,
    min_overall_score=40,
    min_confidence=0.50,
    max_solution_leakage=70
)
```

## Batch Processing & State Tracking

The pipeline uses explicit state tracking for reliable, resumable processing:

```python
# Mark document as processed
db.mark_processing_state(
    doc_id=123,
    stage='extraction',
    status='completed',
    error=None
)

# Get unprocessed documents
unprocessed = db.get_unprocessed_documents(
    stage='extraction',
    limit=10
)
```

## Output & Reporting

### Export Challenges to JSON

```python
import json
from database import Database

db = Database()
db.connect()

challenges = db.get_all_challenges()

output = {
    "total": len(challenges),
    "challenges": [
        {
            "id": c['challenge_id'],
            "title": c['challenge_title'],
            "statement": c['challenge_statement'],
            "sdg_goals": c['sdg_goals'],
            "geography": c['geography'],
            "confidence": float(c['confidence']),
            "score": {
                "overall": c.get('overall_score'),
                "density": c.get('challenge_density'),
                "specificity": c.get('specificity')
            }
        }
        for c in challenges
    ]
}

with open('challenges_export.json', 'w') as f:
    json.dump(output, f, indent=2)

db.disconnect()
```

## Troubleshooting

### Database Connection Error

```
psycopg2.OperationalError: could not connect to server
```

**Solution**: Ensure PostgreSQL is running and credentials in `.env` are correct.

```bash
sudo service postgresql start
psql -U postgres -h localhost -d sdg_challenges
```

### LLM API Error

```
openai.error.AuthenticationError: Invalid API key
```

**Solution**: Check `OPENAI_API_KEY` in `.env`.

### No Challenges Extracted

**Possible causes**:
1. Documents have no text content (PDF extraction failed)
2. LLM is filtering out content as too solution-heavy
3. Chunks are too small or too large

**Solution**: Check logs and adjust `CHUNK_SIZE` in `.env`.

## Performance Optimization

### For Large-Scale Processing

1. **Increase batch size**: `BATCH_SIZE=50` in `.env`
2. **Parallel processing**: Modify `pipeline.py` to use `multiprocessing.Pool`
3. **Add database indexes**: Already included in schema
4. **Cache LLM responses**: Implement caching for repeated chunks

### Database Optimization

```sql
-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM challenge WHERE overall_score > 60;

-- Vacuum and analyze
VACUUM ANALYZE;

-- Check index usage
SELECT * FROM pg_stat_user_indexes;
```

## Future Enhancements

### Phase 2 Features (Post-MVP)

- [ ] Embeddings and semantic deduplication (pgvector)
- [ ] Human review UI for challenge validation
- [ ] Scheduled recrawls with change detection
- [ ] Advanced crawl policies (robots.txt, rate limiting)
- [ ] Search query generation for new source discovery
- [ ] REST API for challenge queries
- [ ] Dashboard for monitoring and analytics

## Contributing

To extend the pipeline:

1. Add new crawlers in `crawler.py`
2. Implement custom scoring in `scorer.py`
3. Add new extraction prompts in `extractor.py`
4. Extend database schema in `schema.sql`

## License

MIT License

## Support

For issues or questions:
1. Check logs in `pipeline.log`
2. Review database state: `SELECT * FROM processing_state WHERE status = 'failed';`
3. Test individual components in isolation

## Citation

If you use this pipeline in research, please cite:

```bibtex
@software{sdg_challenge_pipeline_2024,
  title={SDG Challenge Extraction Pipeline},
  author={Your Name},
  year={2024},
  url={https://github.com/your-repo/sdg-challenge-pipeline}
}
```
