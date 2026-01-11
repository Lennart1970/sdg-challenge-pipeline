# Supabase Setup Guide

Complete guide for setting up the SDG Challenge Pipeline with Supabase as your database.

---

## Why Supabase?

**Supabase** is an open-source Firebase alternative that provides:

✅ **Managed PostgreSQL** - No server setup or maintenance  
✅ **Automatic backups** - Daily backups included  
✅ **Built-in API** - RESTful and GraphQL APIs auto-generated  
✅ **Real-time subscriptions** - Live data updates  
✅ **Authentication** - Built-in user management (optional)  
✅ **Free tier** - 500MB database, 2GB bandwidth/month  
✅ **Easy scaling** - Upgrade as you grow  

---

## Part 1: Create Supabase Project

### 1. Sign Up for Supabase

1. Go to [supabase.com](https://supabase.com)
2. Click **Start your project**
3. Sign in with GitHub (recommended) or email

### 2. Create New Project

1. Click **New Project**
2. Fill in details:
   - **Name**: `sdg-challenge-pipeline`
   - **Database Password**: Generate a strong password (save this!)
   - **Region**: Choose closest to your location
   - **Pricing Plan**: Free (or Pro if needed)
3. Click **Create new project**
4. Wait 2-3 minutes for provisioning

### 3. Get Your Connection Details

Once your project is ready:

1. Go to **Settings** → **Database**
2. Scroll to **Connection string** section
3. Copy the **URI** connection string:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
   ```
4. Replace `[YOUR-PASSWORD]` with your actual database password

### 4. Get Your API Keys

1. Go to **Settings** → **API**
2. Copy these values:
   - **Project URL**: `https://[YOUR-PROJECT-REF].supabase.co`
   - **anon public** key (for API access)
   - **service_role** key (for admin access)

---

## Part 2: Initialize Database Schema

### Option A: Using Supabase SQL Editor (Recommended)

1. In Supabase Dashboard, go to **SQL Editor**
2. Click **New query**
3. Copy the entire contents of `schema.sql` from the repository
4. Paste into the SQL editor
5. Click **Run** (or press Ctrl+Enter)
6. Verify tables were created: Go to **Table Editor** and you should see all 8 tables

### Option B: Using Local psql Client

```bash
# Install psql if not already installed
sudo apt-get install postgresql-client

# Connect to Supabase
psql "postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres"

# In psql prompt, load schema
\i schema.sql

# Verify tables
\dt

# Exit
\q
```

---

## Part 3: Configure Your Project

### 1. Update .env File

```bash
# Copy example
cp .env.example .env

# Edit with your editor
nano .env
```

### 2. Add Your Supabase Credentials

```env
# Database Configuration - Supabase
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
SUPABASE_URL=https://[YOUR-PROJECT-REF].supabase.co
SUPABASE_KEY=your_supabase_anon_key

# LLM Configuration
OPENAI_API_KEY=your_openai_api_key_here
LLM_MODEL=gpt-4.1-mini
LLM_TEMPERATURE=0.3

# Crawler Configuration
CRAWLER_TIMEOUT=30
CRAWLER_MAX_RETRIES=3

# Processing Configuration
BATCH_SIZE=10
MAX_WORKERS=4

# Logging
LOG_LEVEL=INFO
LOG_FILE=pipeline.log
```

**Replace these placeholders:**
- `[YOUR-PASSWORD]` - Your Supabase database password
- `[YOUR-PROJECT-REF]` - Your project reference (e.g., `abcdefghijklmnop`)
- `your_supabase_anon_key` - Your anon public key from Supabase
- `your_openai_api_key_here` - Your OpenAI API key

---

## Part 4: Test Connection

### Quick Test

```bash
# Activate virtual environment (if using one)
source venv/bin/activate

# Test database connection
python3 -c "from database import Database; db = Database(); db.connect(); print('✓ Connected to Supabase!'); db.disconnect()"
```

### Run Full Test Suite

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

---

## Part 5: Run the Pipeline

```bash
# Run the pipeline
python3 pipeline.py
```

This will:
1. Seed 18 organizations and 18 source feeds
2. Discover and fetch documents
3. Extract challenges using LLM
4. Deduplicate and score challenges

---

## Part 6: View Your Data in Supabase

### Using Supabase Dashboard

1. Go to **Table Editor**
2. Browse your tables:
   - **org** - Organizations
   - **source_feed** - Data sources
   - **raw_document** - Fetched documents
   - **challenge** - Extracted challenges
   - **challenge_score** - Quality scores

### Using SQL Editor

```sql
-- View all challenges
SELECT 
  challenge_title, 
  challenge_statement, 
  confidence,
  sdg_goals,
  geography
FROM challenge
ORDER BY extracted_at DESC
LIMIT 10;

-- Get statistics
SELECT 
  COUNT(*) as total_challenges,
  AVG(confidence) as avg_confidence,
  COUNT(DISTINCT org_id) as num_organizations
FROM challenge;

-- View top-scored challenges
SELECT 
  c.challenge_title,
  c.challenge_statement,
  cs.overall_score
FROM challenge c
JOIN challenge_score cs ON c.challenge_id = cs.challenge_id
ORDER BY cs.overall_score DESC
LIMIT 10;
```

---

## Part 7: Enable Row Level Security (Optional)

For production deployments, enable RLS:

### 1. Enable RLS on Tables

In SQL Editor:

```sql
-- Enable RLS on all tables
ALTER TABLE org ENABLE ROW LEVEL SECURITY;
ALTER TABLE source_feed ENABLE ROW LEVEL SECURITY;
ALTER TABLE raw_document ENABLE ROW LEVEL SECURITY;
ALTER TABLE challenge ENABLE ROW LEVEL SECURITY;
ALTER TABLE initiative ENABLE ROW LEVEL SECURITY;
ALTER TABLE initiative_challenge ENABLE ROW LEVEL SECURITY;
ALTER TABLE challenge_score ENABLE ROW LEVEL SECURITY;
ALTER TABLE processing_state ENABLE ROW LEVEL SECURITY;
```

### 2. Create Policies

```sql
-- Allow service role to do everything
CREATE POLICY "Service role has full access" ON challenge
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- Repeat for other tables as needed
```

### 3. Update .env to Use Service Role Key

```env
SUPABASE_KEY=your_supabase_service_role_key
```

---

## Part 8: Monitoring and Maintenance

### View Database Usage

1. Go to **Settings** → **Usage**
2. Monitor:
   - Database size
   - Bandwidth usage
   - API requests

### View Logs

1. Go to **Logs** → **Postgres Logs**
2. Filter by severity or search for errors

### Backup and Restore

**Automatic Backups** (included):
- Daily backups for 7 days (Free tier)
- Point-in-time recovery (Pro tier)

**Manual Backup**:

```bash
# Export database
pg_dump "postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres" > backup.sql

# Restore
psql "postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres" < backup.sql
```

---

## Part 9: Scaling and Performance

### Free Tier Limits

- **Database**: 500 MB
- **Bandwidth**: 2 GB/month
- **API requests**: Unlimited
- **Connections**: 60 direct, 200 pooled

### Upgrade When Needed

**Pro Plan** ($25/month):
- 8 GB database
- 250 GB bandwidth
- Point-in-time recovery
- Daily backups for 30 days
- Priority support

### Optimize Performance

1. **Add Indexes** (already included in schema.sql):
   ```sql
   CREATE INDEX IF NOT EXISTS challenge_score_idx ON challenge(overall_score DESC);
   ```

2. **Use Connection Pooling** (built-in):
   - Supabase automatically pools connections
   - Use `?pgbouncer=true` in connection string for session mode

3. **Enable Caching**:
   - Use Supabase's built-in caching for API calls
   - Cache frequently accessed data in your application

---

## Part 10: Troubleshooting

### Issue: Connection Timeout

**Solution**:
```bash
# Check if your IP is allowed
# Supabase allows all IPs by default, but check firewall settings

# Test connection
psql "postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres" -c "SELECT 1"
```

### Issue: Authentication Failed

**Solution**:
- Verify password is correct
- Check DATABASE_URL format
- Ensure no special characters need URL encoding

### Issue: Table Not Found

**Solution**:
```sql
-- Re-run schema
\i schema.sql

-- Or in Supabase SQL Editor, paste schema.sql contents and run
```

### Issue: Rate Limiting

**Solution**:
- Reduce BATCH_SIZE in .env
- Add delays between API calls
- Consider upgrading to Pro plan

---

## Part 11: Using Supabase API (Optional)

### Install Supabase Client

```bash
pip install supabase
```

### Query via API

```python
from supabase import create_client, Client

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Query challenges
response = supabase.table('challenge').select('*').limit(10).execute()
challenges = response.data

for c in challenges:
    print(c['challenge_title'])
```

---

## Part 12: Migration from Local PostgreSQL

If you're migrating from local PostgreSQL:

### 1. Export Data

```bash
# Export from local database
pg_dump -U postgres sdg_challenges > local_backup.sql
```

### 2. Import to Supabase

```bash
# Import to Supabase
psql "postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres" < local_backup.sql
```

### 3. Update .env

```env
# Comment out local config
# DB_HOST=localhost
# DB_USER=postgres

# Add Supabase config
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
```

---

## Quick Reference

### Connection String Format

```
postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
```

### Essential Commands

```bash
# Test connection
python3 -c "from database import Database; db = Database(); db.connect(); print('Connected!'); db.disconnect()"

# Run pipeline
python3 pipeline.py

# View logs
tail -f pipeline.log

# Connect via psql
psql "postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres"
```

### Supabase Dashboard URLs

- **Project Dashboard**: `https://supabase.com/dashboard/project/[PROJECT-REF]`
- **Table Editor**: `https://supabase.com/dashboard/project/[PROJECT-REF]/editor`
- **SQL Editor**: `https://supabase.com/dashboard/project/[PROJECT-REF]/sql`
- **API Docs**: `https://supabase.com/dashboard/project/[PROJECT-REF]/api`

---

## Cost Comparison

### Free Tier (Supabase)
- **Cost**: $0/month
- **Database**: 500 MB
- **Bandwidth**: 2 GB/month
- **Perfect for**: Development, testing, small projects

### Pro Tier (Supabase)
- **Cost**: $25/month
- **Database**: 8 GB
- **Bandwidth**: 250 GB/month
- **Perfect for**: Production, growing projects

### vs. Google Cloud VM + PostgreSQL
- **Cost**: $37-52/month
- **Maintenance**: Manual setup, updates, backups
- **Supabase advantage**: Managed, automatic backups, easier scaling

---

## Security Best Practices

1. **Never commit .env to Git** (already in .gitignore)
2. **Use service_role key** only in secure environments
3. **Enable RLS** for production
4. **Rotate keys** periodically
5. **Monitor usage** for unusual activity
6. **Use connection pooling** to prevent connection exhaustion

---

## Support and Resources

- **Supabase Docs**: https://supabase.com/docs
- **Supabase Discord**: https://discord.supabase.com
- **GitHub Issues**: https://github.com/Lennart1970/sdg-challenge-pipeline/issues
- **Project Docs**: See [README.md](README.md) and [QUICKSTART.md](QUICKSTART.md)

---

**Managed. Scalable. Ready in minutes.**
