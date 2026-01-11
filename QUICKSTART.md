# Quick Start Guide

Get the SDG Challenge Extraction Pipeline running in 5 minutes.

## Prerequisites

- Python 3.8+
- PostgreSQL 12+
- OpenAI API key

## Installation

```bash
# Clone the repository
git clone https://github.com/Lennart1970/sdg-challenge-pipeline.git
cd sdg-challenge-pipeline

# Install dependencies
pip install -r requirements.txt

# Download NLTK data
python3 -c "import nltk; nltk.download('stopwords')"
```

## Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env
```

**Required settings**:
```env
OPENAI_API_KEY=your_api_key_here
DB_NAME=sdg_challenges
DB_USER=postgres
DB_PASSWORD=
```

## Database Setup

```bash
# Create database
sudo -u postgres createdb sdg_challenges

# Initialize schema
sudo -u postgres psql -d sdg_challenges -f schema.sql
```

## Run Tests

```bash
python3 test_pipeline.py
```

Expected output:
```
✓ PASS: Database
✓ PASS: Chunker
✓ PASS: Extractor
✓ PASS: Deduplicator
✓ PASS: Scorer

Total: 5/5 tests passed
✓ All tests passed!
```

## Run the Pipeline

```bash
python3 pipeline.py
```

This will:
1. Seed 18 organizations and 18 source feeds
2. Discover and fetch documents from active feeds
3. Extract challenges using LLM
4. Deduplicate and score challenges

## Query Results

```python
from database import Database

db = Database()
db.connect()

# Get all challenges
challenges = db.get_all_challenges(limit=10)

for c in challenges:
    print(f"Title: {c['challenge_title']}")
    print(f"Statement: {c['challenge_statement']}")
    print(f"SDG Goals: {c['sdg_goals']}")
    print(f"Geography: {c['geography']}")
    print(f"Confidence: {c['confidence']}")
    print()

db.disconnect()
```

## Troubleshooting

### Database connection error

```bash
# Start PostgreSQL
sudo service postgresql start

# Test connection
psql -U postgres -h localhost -d sdg_challenges
```

### OpenAI API error

Check your API key in `.env`:
```bash
echo $OPENAI_API_KEY
```

### No challenges extracted

Check logs:
```bash
tail -f pipeline.log
```

## Next Steps

- Review `README.md` for full documentation
- Customize source feeds in `seed_data.json`
- Adjust scoring weights in `config.py`
- Add new crawlers in `crawler.py`

## Support

- GitHub Issues: https://github.com/Lennart1970/sdg-challenge-pipeline/issues
- Documentation: See `README.md`
