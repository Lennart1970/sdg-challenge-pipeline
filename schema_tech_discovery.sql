-- Technology Discovery Extension Schema
-- Adds tables for storing technology discovery runs and discovered paths

-- Table: tech_discovery_run
-- Stores metadata about each technology discovery run
CREATE TABLE IF NOT EXISTS tech_discovery_run (
    run_id SERIAL PRIMARY KEY,
    challenge_id INTEGER NOT NULL REFERENCES challenge(challenge_id) ON DELETE CASCADE,
    
    -- Discovery metadata
    discovered_at TIMESTAMP NOT NULL DEFAULT NOW(),
    model_used VARCHAR(100),
    budget_constraint_eur INTEGER NOT NULL DEFAULT 10000,
    
    -- Discovery results (full JSON)
    challenge_summary TEXT,
    core_functions JSONB,  -- Array of function strings
    underlying_principles JSONB,  -- Array of principle strings
    confidence DECIMAL(3, 2) CHECK (confidence >= 0 AND confidence <= 1),
    
    -- Full response
    full_response JSONB,  -- Complete structured output from LLM
    
    -- Status tracking
    status VARCHAR(50) DEFAULT 'completed',  -- completed, failed, in_progress
    error_message TEXT,
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Table: tech_path
-- Stores individual technology paths discovered for challenges
CREATE TABLE IF NOT EXISTS tech_path (
    path_id SERIAL PRIMARY KEY,
    run_id INTEGER NOT NULL REFERENCES tech_discovery_run(run_id) ON DELETE CASCADE,
    challenge_id INTEGER NOT NULL REFERENCES challenge(challenge_id) ON DELETE CASCADE,
    
    -- Path details
    path_name VARCHAR(500) NOT NULL,
    path_order INTEGER NOT NULL,  -- Order in the discovery result (1, 2, 3)
    
    -- Technical details
    principles_used JSONB,  -- Array of principle strings
    technology_classes JSONB,  -- Array of technology class strings
    why_plausible TEXT,
    
    -- Cost and feasibility
    estimated_cost_band_eur VARCHAR(100),  -- e.g., "€500-€2000"
    risks_and_unknowns JSONB,  -- Array of risk strings
    
    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(run_id, path_order)
);

-- Indexes for performance

-- Index on challenge_id for finding all discovery runs for a challenge
CREATE INDEX IF NOT EXISTS idx_tech_discovery_run_challenge 
ON tech_discovery_run(challenge_id);

-- Index on discovered_at for time-based queries
CREATE INDEX IF NOT EXISTS idx_tech_discovery_run_discovered_at 
ON tech_discovery_run(discovered_at DESC);

-- Index on status for filtering active/failed runs
CREATE INDEX IF NOT EXISTS idx_tech_discovery_run_status 
ON tech_discovery_run(status);

-- Index on challenge_id for finding all paths for a challenge
CREATE INDEX IF NOT EXISTS idx_tech_path_challenge 
ON tech_path(challenge_id);

-- Index on run_id for finding all paths in a discovery run
CREATE INDEX IF NOT EXISTS idx_tech_path_run 
ON tech_path(run_id);

-- Composite index for efficient path retrieval
CREATE INDEX IF NOT EXISTS idx_tech_path_run_order 
ON tech_path(run_id, path_order);

-- Comments for documentation

COMMENT ON TABLE tech_discovery_run IS 
'Stores technology discovery runs for challenges, including metadata and full LLM response';

COMMENT ON COLUMN tech_discovery_run.challenge_id IS 
'Reference to the challenge being analyzed';

COMMENT ON COLUMN tech_discovery_run.budget_constraint_eur IS 
'Maximum budget constraint applied during discovery (typically €10,000)';

COMMENT ON COLUMN tech_discovery_run.core_functions IS 
'JSON array of core functions identified (what must happen)';

COMMENT ON COLUMN tech_discovery_run.underlying_principles IS 
'JSON array of physical/chemical/mechanical principles';

COMMENT ON COLUMN tech_discovery_run.full_response IS 
'Complete structured JSON response from LLM for traceability';

COMMENT ON TABLE tech_path IS 
'Stores individual technology paths discovered for challenges';

COMMENT ON COLUMN tech_path.path_order IS 
'Order of this path in the discovery result (1=first, 2=second, etc.)';

COMMENT ON COLUMN tech_path.technology_classes IS 
'JSON array of technology classes (NOT brands or products)';

COMMENT ON COLUMN tech_path.estimated_cost_band_eur IS 
'Estimated cost range in euros (e.g., "€500-€2000")';
