# Quick Start Guide

Get the SDG Challenge Pipeline running in 5 minutes with Supabase.

## Prerequisites

- Python 3.8+
- Supabase account (free tier works great!)
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

## Database Setup (Supabase - Recommended)

### 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign up
2. Click **New Project**
3. Set name: `sdg-challenge-pipeline`
4. Generate and save your database password
5. Choose region closest to you
6. Click **Create new project** (wait 2-3 minutes)

### 2. Initialize Database

1. In Supabase Dashboard, go to **SQL Editor**
2. Click **New query**
3. Copy contents of `schema.sql` from the repository
4. Paste and click **Run**
5. Verify tables in **Table Editor**

### 3. Get Connection Details

1. Go to **Settings** → **Database**
2. Copy the **URI** connection string
3. Go to **Settings** → **API**
4. Copy **Project URL** and **anon public** key

## Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env
```

**Add your credentials**:
```env
# Supabase Database
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
SUPABASE_URL=https://[YOUR-PROJECT-REF].supabase.co
SUPABASE_KEY=your_supabase_anon_key

# OpenAI API
OPENAI_API_KEY=your_api_key_here
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

## View Results

### In Supabase Dashboard

1. Go to **Table Editor**
2. Browse tables: `challenge`, `challenge_score`, `org`
3. Use **SQL Editor** for custom queries

### Via Python

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

## Alternative: Local PostgreSQL

If you prefer local PostgreSQL instead of Supabase:

```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Create database
sudo -u postgres createdb sdg_challenges

# Initialize schema
sudo -u postgres psql -d sdg_challenges -f schema.sql

# Update .env
DB_HOST=localhost
DB_NAME=sdg_challenges
DB_USER=postgres
DB_PASSWORD=
```

## Troubleshooting

### Database connection error

**Supabase**:
- Check DATABASE_URL format
- Verify password is correct
- Ensure project is active in Supabase dashboard

**Local PostgreSQL**:
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

- **Full documentation**: See [README.md](README.md)
- **Supabase guide**: See [SUPABASE_SETUP.md](SUPABASE_SETUP.md)
- **Deployment guide**: See [DEPLOYMENT.md](DEPLOYMENT.md)
- **Customize sources**: Edit `seed_data.json`
- **Adjust scoring**: Modify weights in `config.py`

## Support

- **Supabase Setup**: See [SUPABASE_SETUP.md](SUPABASE_SETUP.md)
- **GitHub Issues**: https://github.com/Lennart1970/sdg-challenge-pipeline/issues
- **Supabase Docs**: https://supabase.com/docs

---

**From zero to running in 5 minutes with Supabase!**
