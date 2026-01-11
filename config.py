"""
SDG Challenge Extraction Pipeline - Configuration
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
# Supports both local PostgreSQL and Supabase
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Fallback to individual components if DATABASE_URL not set
if not DATABASE_URL:
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "sdg_challenges")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    
    if DB_PASSWORD:
        DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    else:
        DATABASE_URL = f"postgresql://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Supabase-specific settings
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# LLM Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4.1-mini")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))

# Crawler Configuration
CRAWLER_TIMEOUT = int(os.getenv("CRAWLER_TIMEOUT", "30"))
CRAWLER_USER_AGENT = os.getenv("CRAWLER_USER_AGENT", 
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
CRAWLER_MAX_RETRIES = int(os.getenv("CRAWLER_MAX_RETRIES", "3"))

# Chunking Configuration
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = float(os.getenv("CHUNK_OVERLAP", "0.15"))

# Scoring Configuration
CHALLENGE_DENSITY_WEIGHT = 0.35
SPECIFICITY_WEIGHT = 0.25
EVIDENCE_WEIGHT = 0.20
RECENCY_WEIGHT = 0.10
SOLUTION_LEAKAGE_WEIGHT = -0.20

# Confidence thresholds
MIN_CONFIDENCE = 0.50
MIN_OVERALL_SCORE = 40
MAX_SOLUTION_LEAKAGE = 70

# Processing Configuration
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10"))
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "pipeline.log")

# Paths
SEED_DATA_PATH = "seed_data.json"
OUTPUT_DIR = "output"
CACHE_DIR = "cache"

# Keywords for challenge detection
CHALLENGE_KEYWORDS_EN = {
    "barrier", "barriers", "constraint", "constraints", "bottleneck", "bottlenecks",
    "gap", "gaps", "unmet need", "unmet needs", "risk", "risks", "vulnerability",
    "vulnerabilities", "inequality", "shortage", "lack of", "needs assessment",
    "baseline", "problem statement", "context", "rationale", "challenge", "challenges"
}

CHALLENGE_KEYWORDS_NL = {
    "uitdaging", "uitdagingen", "knelpunt", "knelpunten", "belemmering", "belemmeringen",
    "gat", "gaten", "onvervulde behoefte", "onvervulde behoeften", "risico", "risico's",
    "kwetsbaarheid", "ongelijkheid", "tekort", "gebrek aan", "behoefteanalyse",
    "basislijnstudie", "probleemstelling", "context", "rationale"
}

SOLUTION_KEYWORDS_EN = {
    "will implement", "will develop", "solution", "technology", "deploy", "rollout",
    "build a platform", "deliver a tool", "pilot", "prototype", "intervention",
    "implement", "develop", "deployment", "launch", "introduce", "establish"
}

SOLUTION_KEYWORDS_NL = {
    "we gaan", "implementeren", "ontwikkelen", "uitrollen", "pilot", "prototype",
    "zullen", "gaan", "platform", "tool", "interventie", "lanceren", "introduceren"
}
