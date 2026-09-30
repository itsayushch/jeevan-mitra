from sqlite3 import Connection
import uuid
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

class QualificationCatalogueService:
    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def get_qualifications(conn: Connection, sector: Optional[str] = None, limit: int = 20) -> List[Dict]:
        query = "SELECT * FROM qualifications WHERE verification_status = 'VERIFIED'"
        params = []
        if sector:
            query += " AND sector = ?"
            params.append(sector)
        query += " LIMIT ?"
        params.append(limit)
        
        cursor = conn.execute(query, tuple(params))
        rows = cursor.fetchall()
        result = []
        for row in rows:
            d = dict(row)
            d['entry_requirements_json'] = json.loads(d['entry_requirements_json']) if d['entry_requirements_json'] else None
            d['skills_json'] = json.loads(d['skills_json']) if d['skills_json'] else None
            result.append(d)
        return result

    @staticmethod
    def get_qualification(conn: Connection, qual_id: str) -> Optional[Dict]:
        row = conn.execute("SELECT * FROM qualifications WHERE id = ?", (qual_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d['entry_requirements_json'] = json.loads(d['entry_requirements_json']) if d['entry_requirements_json'] else None
        d['skills_json'] = json.loads(d['skills_json']) if d['skills_json'] else None
        return d

    @staticmethod
    def create_qualification(conn: Connection, data: Dict, user_id: str) -> Dict:
        qual_id = f"qual_{uuid.uuid4().hex[:8]}"
        now = QualificationCatalogueService._now()
        
        entry_json = json.dumps(data.get('entry_requirements_json')) if data.get('entry_requirements_json') else None
        skills_json = json.dumps(data.get('skills_json')) if data.get('skills_json') else None
        
        conn.execute("""
            INSERT INTO qualifications (
                id, external_reference, title, description, sector, nsqf_level, duration_hours,
                entry_requirements_json, skills_json, source_name, source_url, source_version,
                source_verified_at, verification_status, created_by_user_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            qual_id, data.get('external_reference'), data['title'], data['description'], data['sector'],
            data.get('nsqf_level'), data.get('duration_hours'), entry_json, skills_json,
            data['source_name'], data.get('source_url'), data.get('source_version'),
            data['source_verified_at'], data.get('verification_status', 'DRAFT'), user_id, now, now
        ))
        
        return QualificationCatalogueService.get_qualification(conn, qual_id)

    @staticmethod
    def update_qualification(conn: Connection, qual_id: str, data: Dict, user_id: str) -> Dict:
        now = QualificationCatalogueService._now()
        updates = []
        params = []
        for k, v in data.items():
            if k in ['title', 'description', 'verification_status']:
                updates.append(f"{k} = ?")
                params.append(v)
        if updates:
            updates.append("updated_at = ?")
            params.append(now)
            params.append(qual_id)
            query = f"UPDATE qualifications SET {', '.join(updates)} WHERE id = ?"
            conn.execute(query, tuple(params))
            
        return QualificationCatalogueService.get_qualification(conn, qual_id)
