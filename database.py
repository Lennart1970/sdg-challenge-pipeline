"""\nDatabase connection and operations module\nSupports both local PostgreSQL and Supabase\n"""

import json
import logging
from typing import Optional, List, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
from config import DATABASE_URL, SEED_DATA_PATH

logger = logging.getLogger(__name__)


class Database:
    """PostgreSQL database connection and operations"""
    
    def __init__(self, db_url: str = DATABASE_URL):
        self.db_url = db_url
        self.conn = None
        
    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(self.db_url)
            logger.info("Connected to database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
            
    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Disconnected from database")
            
    def execute(self, query: str, params: tuple = None, fetch: bool = False):
        """Execute a query"""
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, params or ())
            
            if fetch:
                result = cursor.fetchall()
            else:
                self.conn.commit()
                result = cursor.rowcount
                
            cursor.close()
            return result
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Query execution failed: {e}")
            raise
            
    def seed_organizations(self, seed_file: str = SEED_DATA_PATH):
        """Load seed data into organizations and source_feeds tables"""
        try:
            with open(seed_file, 'r') as f:
                data = json.load(f)
                
            # Insert organizations
            org_mapping = {}
            for org in data['organizations']:
                query = """
                    INSERT INTO org (org_name, org_type, org_country, org_website)
                    VALUES (%s, %s, %s, %s)
                    RETURNING org_id
                """
                cursor = self.conn.cursor()
                cursor.execute(query, (
                    org['org_name'],
                    org['org_type'],
                    org.get('org_country'),
                    org.get('org_website')
                ))
                org_id = cursor.fetchone()[0]
                org_mapping[org['org_name']] = org_id
                cursor.close()
                
            logger.info(f"Inserted {len(org_mapping)} organizations")
            
            # Insert source feeds
            for feed in data['source_feeds']:
                org_id = org_mapping.get(feed['org_name'])
                if not org_id:
                    logger.warning(f"Organization not found for feed: {feed['feed_name']}")
                    continue
                    
                query = """
                    INSERT INTO source_feed (org_id, feed_name, feed_type, base_url, crawl_policy, active)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor = self.conn.cursor()
                cursor.execute(query, (
                    org_id,
                    feed['feed_name'],
                    feed['feed_type'],
                    feed.get('base_url'),
                    json.dumps(feed.get('crawl_policy', {})),
                    True
                ))
                cursor.close()
                
            self.conn.commit()
            logger.info(f"Inserted {len(data['source_feeds'])} source feeds")
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to seed data: {e}")
            raise
            
    def insert_raw_document(self, feed_id: int, url: str, **kwargs) -> int:
        """Insert a raw document record"""
        query = """
            INSERT INTO raw_document 
            (feed_id, url, canonical_url, http_status, content_type, lang, title, 
             hash_sha256, text_content, metadata, crawl_depth, parent_url, is_primary_source, error)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING doc_id
        """
        cursor = self.conn.cursor()
        cursor.execute(query, (
            feed_id,
            url,
            kwargs.get('canonical_url'),
            kwargs.get('http_status'),
            kwargs.get('content_type'),
            kwargs.get('lang'),
            kwargs.get('title'),
            kwargs.get('hash_sha256'),
            kwargs.get('text_content'),
            json.dumps(kwargs.get('metadata', {})),
            kwargs.get('crawl_depth', 0),
            kwargs.get('parent_url'),
            kwargs.get('is_primary_source', True),
            kwargs.get('error')
        ))
        doc_id = cursor.fetchone()[0]
        cursor.close()
        self.conn.commit()
        return doc_id
        
    def insert_challenge(self, doc_id: int, org_id: int, **kwargs) -> int:
        """Insert a challenge record"""
        query = """
            INSERT INTO challenge 
            (doc_id, org_id, challenge_title, challenge_statement, sdg_goals, geography,
             target_groups, sectors, scale_numbers, root_causes, constraints, evidence_quotes,
             confidence, extraction_model, statement_fingerprint)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING challenge_id
        """
        cursor = self.conn.cursor()
        cursor.execute(query, (
            doc_id,
            org_id,
            kwargs.get('challenge_title'),
            kwargs['challenge_statement'],
            kwargs.get('sdg_goals', []),
            kwargs.get('geography'),
            kwargs.get('target_groups', []),
            kwargs.get('sectors', []),
            json.dumps(kwargs.get('scale_numbers', {})),
            kwargs.get('root_causes', []),
            kwargs.get('constraints', []),
            kwargs.get('evidence_quotes', []),
            kwargs.get('confidence', 0.70),
            kwargs.get('extraction_model'),
            kwargs.get('statement_fingerprint')
        ))
        challenge_id = cursor.fetchone()[0]
        cursor.close()
        self.conn.commit()
        return challenge_id
        
    def insert_challenge_score(self, challenge_id: int, **kwargs):
        """Insert challenge scoring record"""
        query = """
            INSERT INTO challenge_score 
            (challenge_id, challenge_density, solution_leakage, specificity, 
             evidence_strength, recency_score, overall_score, scoring_notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (challenge_id) DO UPDATE SET
                challenge_density = EXCLUDED.challenge_density,
                solution_leakage = EXCLUDED.solution_leakage,
                specificity = EXCLUDED.specificity,
                evidence_strength = EXCLUDED.evidence_strength,
                recency_score = EXCLUDED.recency_score,
                overall_score = EXCLUDED.overall_score,
                scoring_notes = EXCLUDED.scoring_notes
        """
        cursor = self.conn.cursor()
        cursor.execute(query, (
            challenge_id,
            kwargs.get('challenge_density'),
            kwargs.get('solution_leakage'),
            kwargs.get('specificity'),
            kwargs.get('evidence_strength'),
            kwargs.get('recency_score'),
            kwargs.get('overall_score'),
            kwargs.get('scoring_notes')
        ))
        cursor.close()
        self.conn.commit()
        
    def get_unprocessed_documents(self, stage: str, limit: int = 10) -> List[Dict]:
        """Get documents that haven't been processed at a given stage"""
        query = """
            SELECT rd.doc_id, rd.feed_id, rd.url, rd.text_content, rd.metadata, 
                   sf.org_id, o.org_name
            FROM raw_document rd
            JOIN source_feed sf ON rd.feed_id = sf.feed_id
            JOIN org o ON sf.org_id = o.org_id
            LEFT JOIN processing_state ps ON rd.doc_id = ps.doc_id AND ps.stage = %s
            WHERE ps.state_id IS NULL AND rd.text_content IS NOT NULL
            LIMIT %s
        """
        return self.execute(query, (stage, limit), fetch=True)
        
    def mark_processing_state(self, doc_id: int, stage: str, status: str, error: str = None):
        """Mark a document as processed at a given stage"""
        query = """
            INSERT INTO processing_state (doc_id, stage, status, error_message)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (doc_id, stage) DO UPDATE SET
                status = EXCLUDED.status,
                error_message = EXCLUDED.error_message,
                processed_at = NOW()
        """
        cursor = self.conn.cursor()
        cursor.execute(query, (doc_id, stage, status, error))
        cursor.close()
        self.conn.commit()
        
    def get_challenges_by_fingerprint(self, fingerprint: str) -> List[Dict]:
        """Get all challenges with the same fingerprint"""
        query = """
            SELECT challenge_id, doc_id, org_id, challenge_statement, confidence, 
                   evidence_quotes, root_causes, constraints
            FROM challenge
            WHERE statement_fingerprint = %s
            ORDER BY confidence DESC, extracted_at DESC
        """
        return self.execute(query, (fingerprint,), fetch=True)
        
    def delete_challenge(self, challenge_id: int):
        """Delete a challenge record"""
        query = "DELETE FROM challenge WHERE challenge_id = %s"
        self.execute(query, (challenge_id,))
        
    def get_all_challenges(self, limit: int = None) -> List[Dict]:
        """Get all challenges"""
        query = "SELECT * FROM challenge ORDER BY extracted_at DESC"
        if limit:
            query += f" LIMIT {limit}"
        return self.execute(query, fetch=True)


    # ==========================================
    # Technology Discovery Methods
    # ==========================================
    
    def insert_tech_discovery_run(
        self,
        challenge_id: int,
        model_used: str,
        budget_constraint_eur: int,
        challenge_summary: str,
        core_functions: List[str],
        underlying_principles: List[str],
        confidence: float,
        full_response: Dict[str, Any],
        status: str = 'completed',
        error_message: Optional[str] = None
    ) -> int:
        """
        Insert a technology discovery run
        
        Args:
            challenge_id: Challenge ID
            model_used: LLM model used
            budget_constraint_eur: Budget constraint in euros
            challenge_summary: Summary of challenge
            core_functions: List of core functions
            underlying_principles: List of underlying principles
            confidence: Confidence score (0-1)
            full_response: Full JSON response from LLM
            status: Run status
            error_message: Optional error message
            
        Returns:
            run_id of inserted discovery run
        """
        query = """
            INSERT INTO tech_discovery_run (
                challenge_id, model_used, budget_constraint_eur,
                challenge_summary, core_functions, underlying_principles,
                confidence, full_response, status, error_message
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING run_id
        """
        
        result = self.execute(
            query,
            (
                challenge_id, model_used, budget_constraint_eur,
                challenge_summary,
                json.dumps(core_functions),
                json.dumps(underlying_principles),
                confidence,
                json.dumps(full_response),
                status,
                error_message
            ),
            fetch=True
        )
        
        run_id = result[0]['run_id']
        logger.info(f"Inserted tech discovery run: {run_id}")
        return run_id
    
    def insert_tech_path(
        self,
        run_id: int,
        challenge_id: int,
        path_name: str,
        path_order: int,
        principles_used: List[str],
        technology_classes: List[str],
        why_plausible: str,
        estimated_cost_band_eur: str,
        risks_and_unknowns: List[str]
    ) -> int:
        """
        Insert a technology path
        
        Args:
            run_id: Discovery run ID
            challenge_id: Challenge ID
            path_name: Name of the path
            path_order: Order in discovery result
            principles_used: List of principles used
            technology_classes: List of technology classes
            why_plausible: Explanation of plausibility
            estimated_cost_band_eur: Cost band string
            risks_and_unknowns: List of risks
            
        Returns:
            path_id of inserted path
        """
        query = """
            INSERT INTO tech_path (
                run_id, challenge_id, path_name, path_order,
                principles_used, technology_classes, why_plausible,
                estimated_cost_band_eur, risks_and_unknowns
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING path_id
        """
        
        result = self.execute(
            query,
            (
                run_id, challenge_id, path_name, path_order,
                json.dumps(principles_used),
                json.dumps(technology_classes),
                why_plausible,
                estimated_cost_band_eur,
                json.dumps(risks_and_unknowns)
            ),
            fetch=True
        )
        
        path_id = result[0]['path_id']
        logger.info(f"Inserted tech path: {path_id}")
        return path_id
    
    def get_tech_discovery_runs(
        self,
        challenge_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get technology discovery runs
        
        Args:
            challenge_id: Optional filter by challenge ID
            status: Optional filter by status
            limit: Maximum number of results
            
        Returns:
            List of discovery run dictionaries
        """
        conditions = []
        params = []
        
        if challenge_id is not None:
            conditions.append("challenge_id = %s")
            params.append(challenge_id)
        
        if status is not None:
            conditions.append("status = %s")
            params.append(status)
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        params.append(limit)
        
        query = f"""
            SELECT * FROM tech_discovery_run
            {where_clause}
            ORDER BY discovered_at DESC
            LIMIT %s
        """
        
        return self.execute(query, tuple(params), fetch=True)
    
    def get_tech_paths(
        self,
        run_id: Optional[int] = None,
        challenge_id: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get technology paths
        
        Args:
            run_id: Optional filter by run ID
            challenge_id: Optional filter by challenge ID
            limit: Maximum number of results
            
        Returns:
            List of tech path dictionaries
        """
        conditions = []
        params = []
        
        if run_id is not None:
            conditions.append("run_id = %s")
            params.append(run_id)
        
        if challenge_id is not None:
            conditions.append("challenge_id = %s")
            params.append(challenge_id)
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        params.append(limit)
        
        query = f"""
            SELECT * FROM tech_path
            {where_clause}
            ORDER BY run_id DESC, path_order ASC
            LIMIT %s
        """
        
        return self.execute(query, tuple(params), fetch=True)
    
    def get_challenge_with_paths(self, challenge_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a challenge with all its technology paths
        
        Args:
            challenge_id: Challenge ID
            
        Returns:
            Dictionary with challenge and paths, or None if not found
        """
        # Get challenge
        challenge = self.execute(
            "SELECT * FROM challenge WHERE challenge_id = %s",
            (challenge_id,),
            fetch=True
        )
        
        if not challenge:
            return None
        
        challenge_data = dict(challenge[0])
        
        # Get latest discovery run
        runs = self.get_tech_discovery_runs(challenge_id=challenge_id, limit=1)
        
        if runs:
            run = runs[0]
            challenge_data['latest_discovery_run'] = dict(run)
            
            # Get paths for this run
            paths = self.get_tech_paths(run_id=run['run_id'])
            challenge_data['technology_paths'] = [dict(p) for p in paths]
        else:
            challenge_data['latest_discovery_run'] = None
            challenge_data['technology_paths'] = []
        
        return challenge_data
