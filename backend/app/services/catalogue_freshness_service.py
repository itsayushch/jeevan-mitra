from datetime import datetime, timedelta
import sqlite3
from typing import List, Dict, Any
from app.core.settings import settings
from app.database import get_db

class CatalogueFreshnessService:
    @staticmethod
    def get_stale_records() -> Dict[str, Any]:
        with get_db() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Qualifications
            qual_threshold = (datetime.now() - timedelta(days=settings.QUALIFICATION_REVIEW_DAYS)).isoformat()
            cursor.execute('''
                SELECT * FROM qualifications 
                WHERE verification_date < ? OR verification_date IS NULL
            ''', (qual_threshold,))
            stale_quals = [dict(r) for r in cursor.fetchall()]
            
            # Opportunities
            opp_threshold = (datetime.now() - timedelta(days=settings.OPPORTUNITY_REVIEW_DAYS)).isoformat()
            
            # ensure availability column exists, handle if not
            try:
                cursor.execute('''
                    SELECT * FROM local_opportunities 
                    WHERE verified_at < ? OR verified_at IS NULL
                ''', (opp_threshold,))
                stale_opps = [dict(r) for r in cursor.fetchall()]
            except sqlite3.OperationalError:
                stale_opps = []
            
            return {
                "stale_qualifications": stale_quals,
                "stale_opportunities": stale_opps
            }
            
    @staticmethod
    def run_freshness_check() -> Dict[str, int]:
        with get_db() as conn:
            cursor = conn.cursor()
            
            opp_threshold = (datetime.now() - timedelta(days=settings.OPPORTUNITY_REVIEW_DAYS)).isoformat()
            
            updates = 0
            try:
                # Find stale verified_open opportunities
                cursor.execute('''
                    SELECT id FROM local_opportunities 
                    WHERE (verified_at < ? OR verified_at IS NULL) 
                    AND availability = 'verified_open'
                ''', (opp_threshold,))
                stale_opp_ids = [r[0] for r in cursor.fetchall()]
                
                if stale_opp_ids:
                    placeholders = ','.join('?' * len(stale_opp_ids))
                    cursor.execute(f'''
                        UPDATE local_opportunities 
                        SET availability = 'unknown' 
                        WHERE id IN ({placeholders})
                    ''', stale_opp_ids)
                    updates = cursor.rowcount
            except sqlite3.OperationalError:
                pass
            
            return {
                "opportunities_updated": updates
            }
            
    @staticmethod
    def get_system_freshness_stats() -> Dict[str, Any]:
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM qualifications')
            total_quals = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM local_opportunities')
            total_opps = cursor.fetchone()[0]
            
            qual_threshold = (datetime.now() - timedelta(days=settings.QUALIFICATION_REVIEW_DAYS)).isoformat()
            cursor.execute('SELECT COUNT(*) FROM qualifications WHERE verification_date >= ?', (qual_threshold,))
            fresh_quals = cursor.fetchone()[0]
            
            opp_threshold = (datetime.now() - timedelta(days=settings.OPPORTUNITY_REVIEW_DAYS)).isoformat()
            try:
                cursor.execute('SELECT COUNT(*) FROM local_opportunities WHERE verified_at >= ?', (opp_threshold,))
                fresh_opps = cursor.fetchone()[0]
            except sqlite3.OperationalError:
                fresh_opps = 0
            
            return {
                "total_qualifications": total_quals,
                "fresh_qualifications": fresh_quals,
                "stale_qualifications": total_quals - fresh_quals,
                "total_opportunities": total_opps,
                "fresh_opportunities": fresh_opps,
                "stale_opportunities": total_opps - fresh_opps
            }
