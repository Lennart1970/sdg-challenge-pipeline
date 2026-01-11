# Deployment Guide: Google Cloud VM

Complete guide for deploying the SDG Challenge Pipeline on Google Cloud Platform (GCP) VM.

---

## Prerequisites

- Google Cloud Platform account
- Google Cloud VM instance (recommended: e2-standard-2 or higher)
- SSH access to your VM
- OpenAI API key
- (Optional) Visual Studio Code with Remote-SSH extension

---

## Part 1: Google Cloud VM Setup

### Option A: Create New VM Instance

```bash
# Using gcloud CLI
gcloud compute instances create sdg-pipeline-vm \
  --zone=us-central1-a \
  --machine-type=e2-standard-2 \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=50GB \
  --boot-disk-type=pd-standard \
  --tags=http-server,https-server
```

**Or via Google Cloud Console:**

1. Go to **Compute Engine** → **VM instances**
2. Click **Create Instance**
3. Configure:
   - **Name**: `sdg-pipeline-vm`
   - **Region**: Choose closest to you
   - **Machine type**: `e2-standard-2` (2 vCPU, 8 GB memory)
   - **Boot disk**: Ubuntu 22.04 LTS, 50 GB
   - **Firewall**: Allow HTTP/HTTPS traffic (if needed)
4. Click **Create**

### Option B: Use Existing VM

If you already have a VM, ensure it meets these requirements:

- **OS**: Ubuntu 20.04+ or Debian 11+
- **RAM**: Minimum 4 GB (8 GB recommended)
- **Storage**: Minimum 20 GB free space
- **Python**: 3.8+ (usually pre-installed)

---

## Part 2: Connect to Your VM

### Method 1: SSH via Google Cloud Console

1. Go to **Compute Engine** → **VM instances**
2. Click **SSH** button next to your instance
3. Browser-based terminal will open

### Method 2: SSH via Terminal (Mac/Linux)

```bash
# Generate SSH key if you don't have one
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# Add SSH key to GCP
# Copy your public key
cat ~/.ssh/id_rsa.pub

# In GCP Console: Compute Engine → Metadata → SSH Keys → Add SSH Key
# Paste your public key

# Connect
ssh -i ~/.ssh/id_rsa username@EXTERNAL_IP
```

### Method 3: Visual Studio Code Remote-SSH

1. **Install Remote-SSH extension** in VS Code
2. **Add SSH configuration**:
   - Press `F1` → "Remote-SSH: Open SSH Configuration File"
   - Add:
     ```
     Host sdg-pipeline
       HostName YOUR_VM_EXTERNAL_IP
       User YOUR_USERNAME
       IdentityFile ~/.ssh/id_rsa
     ```
3. **Connect**:
   - Press `F1` → "Remote-SSH: Connect to Host"
   - Select `sdg-pipeline`
   - VS Code will connect to your VM

---

## Part 3: Install System Dependencies

Once connected to your VM:

```bash
# Update system packages
sudo apt-get update && sudo apt-get upgrade -y

# Install essential build tools
sudo apt-get install -y \
  build-essential \
  git \
  curl \
  wget \
  vim \
  htop

# Install Python 3.11 (if not already installed)
sudo apt-get install -y python3.11 python3.11-venv python3-pip

# Install PostgreSQL
sudo apt-get install -y postgresql postgresql-contrib

# Start PostgreSQL
sudo service postgresql start

# Enable PostgreSQL to start on boot
sudo systemctl enable postgresql
```

---

## Part 4: Install the Pipeline

### 1. Clone the Repository

```bash
# Navigate to home directory
cd ~

# Clone the repository
git clone https://github.com/Lennart1970/sdg-challenge-pipeline.git

# Navigate to project directory
cd sdg-challenge-pipeline
```

### 2. Set Up Python Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### 3. Install Python Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# Download NLTK data
python3 -c "import nltk; nltk.download('stopwords')"
```

---

## Part 5: Configure PostgreSQL

### 1. Create Database and User

```bash
# Switch to postgres user
sudo -u postgres psql

# In PostgreSQL prompt, run:
CREATE DATABASE sdg_challenges;
CREATE USER sdg_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE sdg_challenges TO sdg_user;
\q
```

### 2. Initialize Database Schema

```bash
# Load schema
sudo -u postgres psql -d sdg_challenges -f schema.sql

# Verify tables were created
sudo -u postgres psql -d sdg_challenges -c "\dt"
```

### 3. Configure PostgreSQL for Local Access

```bash
# Edit pg_hba.conf
sudo nano /etc/postgresql/14/main/pg_hba.conf

# Add this line before other rules:
# local   sdg_challenges    sdg_user                                md5

# Restart PostgreSQL
sudo service postgresql restart
```

---

## Part 6: Configure Environment Variables

### 1. Create .env File

```bash
# Copy example
cp .env.example .env

# Edit with your settings
nano .env
```

### 2. Set Your Configuration

```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sdg_challenges
DB_USER=sdg_user
DB_PASSWORD=your_secure_password

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

**Important**: Replace `your_openai_api_key_here` with your actual OpenAI API key.

---

## Part 7: Run Tests

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Run test suite
python3 test_pipeline.py
```

**Expected output:**
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

## Part 8: Run the Pipeline

### First Run (Seed Data)

```bash
# Activate virtual environment
source venv/bin/activate

# Run the pipeline
python3 pipeline.py
```

This will:
1. Seed 18 organizations and 18 source feeds
2. Discover URLs from active feeds
3. Fetch and extract documents
4. Extract challenges using LLM
5. Deduplicate and score challenges

**Note**: First run may take 10-30 minutes depending on data volume.

### Monitor Progress

```bash
# In another terminal, watch logs
tail -f pipeline.log
```

---

## Part 9: Query Results

### Using Python

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
    print(f"Score: {c.get('overall_score', 'N/A')}")
    print("-" * 60)

db.disconnect()
```

### Using PostgreSQL CLI

```bash
# Connect to database
sudo -u postgres psql -d sdg_challenges

# Query challenges
SELECT challenge_title, challenge_statement, confidence 
FROM challenge 
ORDER BY extracted_at DESC 
LIMIT 10;

# Check statistics
SELECT 
  COUNT(*) as total_challenges,
  AVG(confidence) as avg_confidence
FROM challenge;

# Exit
\q
```

---

## Part 10: Set Up as a Service (Optional)

To run the pipeline automatically on a schedule:

### Create Systemd Service

```bash
# Create service file
sudo nano /etc/systemd/system/sdg-pipeline.service
```

**Add this content:**

```ini
[Unit]
Description=SDG Challenge Extraction Pipeline
After=network.target postgresql.service

[Service]
Type=oneshot
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/sdg-challenge-pipeline
Environment="PATH=/home/YOUR_USERNAME/sdg-challenge-pipeline/venv/bin"
ExecStart=/home/YOUR_USERNAME/sdg-challenge-pipeline/venv/bin/python3 pipeline.py

[Install]
WantedBy=multi-user.target
```

**Replace `YOUR_USERNAME` with your actual username.**

### Create Timer for Scheduled Runs

```bash
# Create timer file
sudo nano /etc/systemd/system/sdg-pipeline.timer
```

**Add this content:**

```ini
[Unit]
Description=Run SDG Pipeline Daily
Requires=sdg-pipeline.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

### Enable and Start

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable timer
sudo systemctl enable sdg-pipeline.timer

# Start timer
sudo systemctl start sdg-pipeline.timer

# Check status
sudo systemctl status sdg-pipeline.timer
```

---

## Part 11: Visual Studio Code Integration

### 1. Open Project in VS Code

After connecting via Remote-SSH:

```bash
# In VS Code terminal
cd ~/sdg-challenge-pipeline
code .
```

### 2. Install Recommended Extensions

- **Python** (Microsoft)
- **PostgreSQL** (Chris Kolkman)
- **GitLens** (GitKraken)
- **YAML** (Red Hat)

### 3. Configure Python Interpreter

1. Press `F1` → "Python: Select Interpreter"
2. Choose: `./venv/bin/python`

### 4. Debug Configuration

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Pipeline",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/pipeline.py",
      "console": "integratedTerminal",
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    },
    {
      "name": "Python: Tests",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/test_pipeline.py",
      "console": "integratedTerminal"
    }
  ]
}
```

---

## Part 12: Firewall and Security

### Configure Firewall (if needed)

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow PostgreSQL (only if accessing externally)
# sudo ufw allow 5432/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### Secure PostgreSQL

```bash
# Edit postgresql.conf
sudo nano /etc/postgresql/14/main/postgresql.conf

# Ensure this line is set (for local access only):
listen_addresses = 'localhost'

# Restart PostgreSQL
sudo service postgresql restart
```

### Secure API Keys

```bash
# Ensure .env is not readable by others
chmod 600 .env

# Add .env to .gitignore (already done)
```

---

## Part 13: Maintenance and Monitoring

### Check Disk Space

```bash
df -h
```

### Monitor PostgreSQL

```bash
# Check database size
sudo -u postgres psql -d sdg_challenges -c "
SELECT pg_size_pretty(pg_database_size('sdg_challenges'));"

# Check table sizes
sudo -u postgres psql -d sdg_challenges -c "
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

### View Logs

```bash
# Pipeline logs
tail -f pipeline.log

# PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-14-main.log

# System logs
sudo journalctl -u sdg-pipeline.service -f
```

### Backup Database

```bash
# Create backup
sudo -u postgres pg_dump sdg_challenges > backup_$(date +%Y%m%d).sql

# Restore from backup
sudo -u postgres psql -d sdg_challenges < backup_20260111.sql
```

---

## Part 14: Troubleshooting

### Issue: Database Connection Error

```bash
# Check PostgreSQL is running
sudo service postgresql status

# Restart if needed
sudo service postgresql restart

# Check connection
psql -U sdg_user -d sdg_challenges -h localhost
```

### Issue: OpenAI API Error

```bash
# Verify API key is set
echo $OPENAI_API_KEY

# Test API key
python3 -c "from openai import OpenAI; client = OpenAI(); print('API key valid')"
```

### Issue: Out of Memory

```bash
# Check memory usage
free -h

# Reduce batch size in .env
BATCH_SIZE=5
MAX_WORKERS=2
```

### Issue: Disk Full

```bash
# Check disk usage
df -h

# Clean up logs
truncate -s 0 pipeline.log

# Vacuum PostgreSQL
sudo -u postgres psql -d sdg_challenges -c "VACUUM FULL;"
```

---

## Part 15: Updating the Pipeline

### Pull Latest Changes

```bash
cd ~/sdg-challenge-pipeline

# Activate virtual environment
source venv/bin/activate

# Pull updates
git pull origin master

# Update dependencies
pip install -r requirements.txt

# Run tests
python3 test_pipeline.py
```

---

## Quick Reference Commands

```bash
# Activate virtual environment
source ~/sdg-challenge-pipeline/venv/bin/activate

# Run pipeline
cd ~/sdg-challenge-pipeline && python3 pipeline.py

# Run tests
cd ~/sdg-challenge-pipeline && python3 test_pipeline.py

# Check logs
tail -f ~/sdg-challenge-pipeline/pipeline.log

# Connect to database
sudo -u postgres psql -d sdg_challenges

# Restart PostgreSQL
sudo service postgresql restart

# Check service status
sudo systemctl status sdg-pipeline.timer
```

---

## Performance Optimization for Production

### 1. Increase VM Resources

```bash
# Stop VM
gcloud compute instances stop sdg-pipeline-vm

# Change machine type
gcloud compute instances set-machine-type sdg-pipeline-vm \
  --machine-type=e2-standard-4 \
  --zone=us-central1-a

# Start VM
gcloud compute instances start sdg-pipeline-vm
```

### 2. Optimize PostgreSQL

```bash
# Edit postgresql.conf
sudo nano /etc/postgresql/14/main/postgresql.conf

# Increase these values based on your VM RAM:
shared_buffers = 2GB
effective_cache_size = 6GB
maintenance_work_mem = 512MB
work_mem = 16MB

# Restart
sudo service postgresql restart
```

### 3. Enable Connection Pooling

```bash
# Install pgbouncer
sudo apt-get install -y pgbouncer

# Configure (see PostgreSQL documentation)
```

---

## Cost Estimation (Google Cloud)

**e2-standard-2 VM** (2 vCPU, 8 GB RAM):
- **On-demand**: ~$50/month
- **Preemptible**: ~$15/month
- **Committed use (1 year)**: ~$35/month

**Storage** (50 GB standard persistent disk):
- ~$2/month

**Network egress**: Variable based on usage

**Total estimated cost**: $37-52/month for on-demand

---

## Support

- **GitHub Issues**: https://github.com/Lennart1970/sdg-challenge-pipeline/issues
- **Documentation**: See [README.md](README.md) and [QUICKSTART.md](QUICKSTART.md)

---

**Deployed. Tested. Ready for production.**
