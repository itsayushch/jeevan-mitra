import { v4 as uuidv4 } from 'uuid';
import Database from 'better-sqlite3';
import { getDatabase } from '../database/connection.js';
import { DriftAdvisory } from '../types/index.js';

export class MonitoringRepository {
  private db: Database.Database;

  constructor(customDb?: Database.Database) {
    this.db = customDb || getDatabase();
  }

  recordAdvisory(input: Omit<DriftAdvisory, 'id' | 'created_at'>): DriftAdvisory {
    const id = `drift_${uuidv4()}`;
    const now = new Date().toISOString();

    const stmt = this.db.prepare(`
      INSERT INTO drift_advisories (
        id, district, flag_type, severity, headline, evidence,
        suggested_human_action, status, created_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);

    stmt.run(
      id,
      input.district,
      input.flag_type,
      input.severity,
      input.headline,
      JSON.stringify(input.evidence),
      input.suggested_human_action,
      'open',
      now
    );

    return {
      id,
      district: input.district,
      flag_type: input.flag_type,
      severity: input.severity,
      headline: input.headline,
      evidence: input.evidence,
      suggested_human_action: input.suggested_human_action,
      created_at: now,
    };
  }

  listAdvisories(filters?: { district?: string; status?: 'open' | 'acknowledged' | 'resolved' }): DriftAdvisory[] {
    let query = `SELECT * FROM drift_advisories WHERE 1=1`;
    const params: any[] = [];

    if (filters?.district) {
      query += ` AND district = ?`;
      params.push(filters.district);
    }
    if (filters?.status) {
      query += ` AND status = ?`;
      params.push(filters.status);
    }

    query += ` ORDER BY created_at DESC`;

    const stmt = this.db.prepare(query);
    const rows = stmt.all(...params) as any[];

    return rows.map((r) => ({
      id: r.id,
      district: r.district,
      flag_type: r.flag_type,
      severity: r.severity,
      headline: r.headline,
      evidence: JSON.parse(r.evidence || '{}'),
      suggested_human_action: r.suggested_human_action,
      created_at: r.created_at,
    }));
  }

  updateStatus(id: string, status: 'open' | 'acknowledged' | 'resolved'): boolean {
    const stmt = this.db.prepare(`UPDATE drift_advisories SET status = ? WHERE id = ?`);
    const res = stmt.run(status, id);
    return res.changes > 0;
  }
}
