# 🌍 Agentic SDG Challenge → Technology Discovery Engine

## Purpose

This project builds an agentic system that connects real sustainability challenges to feasible technology pathways under €10,000, using existing, widely available technology.

**It does not generate product recommendations.**  
**It does not list solutions.**

Instead, it systematically discovers plausible technology directions by reasoning from:

> **problems → functions → principles → technology classes**

---

## Why This Exists

Across the UN SDGs, governments, NGOs, and corporates have already articulated thousands of well-defined challenges.

At the same time:

- **Low-cost hardware is everywhere**
- **Second-hand machinery is abundant**
- **Open hardware and DIY tooling are mature**
- **Sensors, controllers, and automation are commoditized**

What's missing is the bridge between:

- **Articulated problems**
- **Feasible, human-scale technology**

**This system builds that bridge.**

---

## Core Philosophy

### 1. Problems First

We extract solution-free challenge statements from authoritative sources:

- UN platforms
- Development banks
- EU projects
- Governments
- NGOs
- Corporate sustainability disclosures

### 2. Technology Already Exists

We treat technology sources as signals of feasibility, not catalogs:

- Tech media
- Open hardware communities
- Used machinery marketplaces
- Low-cost electronics platforms

### 3. Discover, Don't Invent

The system discovers what is already possible under constraints instead of inventing novel solutions.

> **Solutions are not created — they are revealed by reframing.**

---

## What the System Does (High Level)

```
CHALLENGE
  ↓
FUNCTIONS (what must happen)
  ↓
PHYSICAL / CHEMICAL / MECHANICAL PRINCIPLES
  ↓
TECHNOLOGY CLASSES (< €10k)
  ↓
PLAUSIBLE TECHNOLOGY PATHS
```

### Example (Simplified)

```
Low-grade wool waste
  → break down structure
  → apply heat + pressure
  → pressure vessel class
  → "high-pressure cooker"-like path
```

**No brands. No SKUs. No premature design.**

---

## What the System Explicitly Does NOT Do

❌ Recommend products  
❌ Optimize designs  
❌ Generate bill of materials  
❌ Promise technical feasibility  
❌ Replace engineering judgment

**It generates directional intelligence, not finished answers.**

---

## Architecture Overview

### Data Layers

#### 1. Challenge Layer (Problem Space)

Stores clean, extracted challenge statements:

- Unmet needs
- Barriers
- Gaps
- Constraints
- Risks

**Source examples:**
- UN SDG platforms
- World Bank project rationales
- EU CORDIS projects
- Government policy gaps
- Corporate material risks

#### 2. Technology Signal Layer (Capability Space)

Stores signals of what is technically and economically plausible:

- Early-stage hardware trends
- Open-source machines
- Cheap industrial equipment
- Used machinery listings
- Commodity electronics platforms

**No solutions are stored — only signals.**

---

## Agents in the System

### 1. Challenge Extractor Agent

- Parses source documents
- Extracts solution-free problem statements
- Structures them into the database

### 2. Technology Discovery Agent

- Takes a challenge as input
- Abstracts it into functions
- Maps functions to principles
- Maps principles to technology classes
- Recombines them into plausible technology paths (< €10k)

**Outputs are conceptual, inspectable, and debuggable.**

---

## Budget Constraint (< €10k)

The **€10,000 cap** is deliberate.

It forces:

- Local feasibility
- Human-scale solutions
- Reuse and recombination
- Creativity within reality

**If something cannot be plausibly achieved under this constraint, it is out of scope.**

---

## Repository Structure

```
/data
  /seeds
    challenges_sources.json
    technology_sources.json

/agents
  challenge_extractor.prompt.md
  technology_discovery_agent.prompt.md

/pipeline
  crawl_sources.py
  extract_challenges.py
  discover_technology_paths.py

/docs
  README.md
  architecture.md
```

---

## How to Use This System

### 1. Seed Sources

- Load challenge sources
- Load technology signal sources

### 2. Ingest Challenges

- Crawl authoritative sources
- Extract clean problem statements

### 3. Run Technology Discovery

- Feed a challenge into the agent
- Receive 2–3 plausible technology paths

### 4. Human Review

- Accept, refine, discard, or explore
- Optionally iterate with new constraints

---

## Intended Use Cases

**Suitable for:**

- Sustainability experimentation
- Circular economy pilots
- Local manufacturing
- SME innovation
- Education & learning paths
- Exploratory R&D
- "What could exist" discovery

**Not intended for:**

- Procurement
- Production engineering
- Compliance certification
- Safety-critical deployment

---

## Mental Model for Contributors

> **This system does not answer:**  
> "What should we build?"

> **It answers:**  
> "Given this problem and these constraints — what is already possible?"

---

## Status

This project is **intentionally exploratory but grounded**.

Accuracy comes from:

- Authoritative problem sources
- Real-world technology signals
- Explicit constraints
- Step-by-step agent reasoning

---

## Contributing

If you contribute:

- **Think in functions, not products**
- **Think in principles, not brands**
- **Think in paths, not answers**

**Clarity beats cleverness. Reality beats novelty.**

---

## Installation & Setup

### Prerequisites

- Python 3.8+
- Supabase account (recommended) or PostgreSQL 12+
- OpenAI API key

### Quick Start

```bash
# Clone the repository
git clone https://github.com/Lennart1970/sdg-challenge-pipeline.git
cd sdg-challenge-pipeline

# Install dependencies
pip install -r requirements.txt

# Download NLTK data
python3 -c "import nltk; nltk.download('stopwords')"

# Configure environment
cp .env.example .env
# Edit .env with your Supabase credentials

# Initialize database (Supabase)
# See SUPABASE_SETUP.md for detailed instructions
# Or use local PostgreSQL:
# sudo -u postgres createdb sdg_challenges
# sudo -u postgres psql -d sdg_challenges -f schema.sql

# Run tests
python3 test_pipeline.py

# Run the pipeline
python3 pipeline.py
```

For detailed setup instructions, see:
- **Supabase Setup**: [SUPABASE_SETUP.md](SUPABASE_SETUP.md) (recommended)
- **Quick Start**: [QUICKSTART.md](QUICKSTART.md)
- **Deployment**: [DEPLOYMENT.md](DEPLOYMENT.md)

---

## Technical Stack

- **Language**: Python 3.11
- **Database**: Supabase (PostgreSQL 15) or PostgreSQL 14+
- **LLM**: OpenAI GPT-4.1-mini
- **Web Scraping**: BeautifulSoup, Requests
- **PDF Processing**: pdfplumber
- **NLP**: NLTK

---

## Project Statistics

- **Lines of Code**: 1,496
- **Python Modules**: 8
- **Database Tables**: 8
- **Test Coverage**: 5/5 (100% passing)
- **Pre-configured Sources**: 18 organizations, 18 feeds

---

## License

MIT License

---

## Support

- **GitHub Issues**: https://github.com/Lennart1970/sdg-challenge-pipeline/issues
- **Supabase Setup**: See [SUPABASE_SETUP.md](SUPABASE_SETUP.md)
- **Quick Start**: See [QUICKSTART.md](QUICKSTART.md)
- **Deployment**: See [DEPLOYMENT.md](DEPLOYMENT.md)

---

**Built with clarity. Grounded in reality. Designed for discovery.**
