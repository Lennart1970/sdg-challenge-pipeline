-- SDG Challenge Extraction Pipeline - Database Schema
-- PostgreSQL 14+ compatible

-- 2.1 Organizations table
CREATE TABLE IF NOT EXISTS org (
  org_id BIGSERIAL PRIMARY KEY,
  org_name TEXT NOT NULL,
  org_type TEXT NOT NULL,
  org_country TEXT,
  org_website TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2.1 Source feeds table
CREATE TABLE IF NOT EXISTS source_feed (
  feed_id BIGSERIAL PRIMARY KEY,
  org_id BIGINT REFERENCES org(org_id) ON DELETE CASCADE,
  feed_name TEXT NOT NULL,
  feed_type TEXT NOT NULL,
  base_url TEXT,
  crawl_policy JSONB,
  active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2.2 Raw documents (fetched pages/PDFs)
CREATE TABLE IF NOT EXISTS raw_document (
  doc_id BIGSERIAL PRIMARY KEY,
  feed_id BIGINT REFERENCES source_feed(feed_id) ON DELETE CASCADE,
  url TEXT NOT NULL,
  canonical_url TEXT,
  fetched_at TIMESTAMPTZ,
  http_status INT,
  content_type TEXT,
  lang TEXT,
  title TEXT,
  hash_sha256 TEXT,
  text_content TEXT,
  metadata JSONB,
  crawl_depth INT DEFAULT 0,
  parent_url TEXT,
  is_primary_source BOOLEAN DEFAULT TRUE,
  error TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS raw_document_url_uq ON raw_document(url);
CREATE INDEX IF NOT EXISTS raw_document_hash_idx ON raw_document(hash_sha256);
CREATE INDEX IF NOT EXISTS raw_document_feed_idx ON raw_document(feed_id);

-- 2.3 Challenge extraction (the product)
CREATE TABLE IF NOT EXISTS challenge (
  challenge_id BIGSERIAL PRIMARY KEY,
  doc_id BIGINT REFERENCES raw_document(doc_id) ON DELETE CASCADE,
  org_id BIGINT REFERENCES org(org_id) ON DELETE CASCADE,
  challenge_title TEXT,
  challenge_statement TEXT NOT NULL,
  sdg_goals INT[],
  geography TEXT,
  target_groups TEXT[],
  sectors TEXT[],
  scale_numbers JSONB,
  root_causes TEXT[],
  constraints TEXT[],
  evidence_quotes TEXT[],
  confidence NUMERIC(3,2) DEFAULT 0.70,
  extraction_model TEXT,
  extracted_at TIMESTAMPTZ DEFAULT NOW(),
  statement_fingerprint TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS challenge_doc_idx ON challenge(doc_id);
CREATE INDEX IF NOT EXISTS challenge_org_idx ON challenge(org_id);
CREATE INDEX IF NOT EXISTS challenge_fingerprint_idx ON challenge(statement_fingerprint);

-- 2.4 Initiatives/projects
CREATE TABLE IF NOT EXISTS initiative (
  initiative_id BIGSERIAL PRIMARY KEY,
  doc_id BIGINT REFERENCES raw_document(doc_id) ON DELETE CASCADE,
  org_id BIGINT REFERENCES org(org_id) ON DELETE CASCADE,
  initiative_name TEXT,
  initiative_type TEXT,
  start_date DATE,
  end_date DATE,
  geography TEXT,
  sdg_goals INT[],
  sectors TEXT[],
  metadata JSONB,
  initiative_fingerprint TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS initiative_org_idx ON initiative(org_id);
CREATE INDEX IF NOT EXISTS initiative_fingerprint_idx ON initiative(initiative_fingerprint);

-- 2.5 Many-to-many: challenge ↔ initiative
CREATE TABLE IF NOT EXISTS initiative_challenge (
  initiative_id BIGINT REFERENCES initiative(initiative_id) ON DELETE CASCADE,
  challenge_id BIGINT REFERENCES challenge(challenge_id) ON DELETE CASCADE,
  PRIMARY KEY (initiative_id, challenge_id)
);

-- 2.6 Challenge scoring & QA
CREATE TABLE IF NOT EXISTS challenge_score (
  challenge_id BIGINT PRIMARY KEY REFERENCES challenge(challenge_id) ON DELETE CASCADE,
  challenge_density INT,
  solution_leakage INT,
  specificity INT,
  evidence_strength INT,
  recency_score INT,
  overall_score INT,
  scored_at TIMESTAMPTZ DEFAULT NOW(),
  scoring_notes TEXT
);

-- 2.7 Processing state tracking (for MVP batch processing)
CREATE TABLE IF NOT EXISTS processing_state (
  state_id BIGSERIAL PRIMARY KEY,
  doc_id BIGINT REFERENCES raw_document(doc_id) ON DELETE CASCADE,
  stage TEXT NOT NULL,
  status TEXT NOT NULL,
  error_message TEXT,
  processed_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(doc_id, stage)
);

CREATE INDEX IF NOT EXISTS processing_state_doc_idx ON processing_state(doc_id);
CREATE INDEX IF NOT EXISTS processing_state_stage_idx ON processing_state(stage);
