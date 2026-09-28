import Database from 'better-sqlite3';
import { getDatabase } from '../database/connection.js';
import { Qualification } from '../types/index.js';

export class QualificationRepository {
  private db: Database.Database;

  constructor(customDb?: Database.Database) {
    this.db = customDb || getDatabase();
  }

  create(input: Qualification): Qualification {
    const stmt = this.db.prepare(`
      INSERT INTO qualifications (
        id, nqr_code, title, sector, nsqf_level, duration_hours,
        min_education, min_education_rank, work_type, physical_intensity,
        skills_acquired, curriculum_summary, entry_criteria, certification_body,
        nqr_link, verification_status, verification_date
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);

    stmt.run(
      input.id,
      input.nqr_code,
      input.title,
      input.sector,
      input.nsqf_level,
      input.duration_hours,
      input.min_education,
      input.min_education_rank,
      input.work_type,
      input.physical_intensity,
      JSON.stringify(input.skills_acquired),
      input.curriculum_summary,
      input.entry_criteria,
      input.certification_body,
      input.nqr_link,
      input.verification_status,
      input.verification_date
    );

    return this.findById(input.id)!;
  }

  findById(id: string): Qualification | null {
    const stmt = this.db.prepare(`SELECT * FROM qualifications WHERE id = ?`);
    const row = stmt.get(id) as any;
    if (!row) return null;
    return this.mapRow(row);
  }

  findByNqrCode(code: string): Qualification | null {
    const stmt = this.db.prepare(`SELECT * FROM qualifications WHERE nqr_code = ?`);
    const row = stmt.get(code) as any;
    if (!row) return null;
    return this.mapRow(row);
  }

  listVerified(): Qualification[] {
    const stmt = this.db.prepare(`
      SELECT * FROM qualifications
      WHERE verification_status = 'verified'
      ORDER BY nsqf_level ASC, title ASC
    `);
    const rows = stmt.all() as any[];
    return rows.map(this.mapRow);
  }

  listBySector(sector: string): Qualification[] {
    const stmt = this.db.prepare(`
      SELECT * FROM qualifications
      WHERE sector = ? AND verification_status = 'verified'
      ORDER BY nsqf_level ASC
    `);
    const rows = stmt.all(sector) as any[];
    return rows.map(this.mapRow);
  }

  private mapRow(row: any): Qualification {
    return {
      id: row.id,
      nqr_code: row.nqr_code,
      title: row.title,
      sector: row.sector,
      nsqf_level: row.nsqf_level,
      duration_hours: row.duration_hours,
      min_education: row.min_education,
      min_education_rank: row.min_education_rank,
      work_type: row.work_type,
      physical_intensity: row.physical_intensity,
      skills_acquired: JSON.parse(row.skills_acquired || '[]'),
      curriculum_summary: row.curriculum_summary,
      entry_criteria: row.entry_criteria,
      certification_body: row.certification_body,
      nqr_link: row.nqr_link,
      verification_status: row.verification_status,
      verification_date: row.verification_date,
    };
  }
}
