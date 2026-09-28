import { v4 as uuidv4 } from 'uuid';
import Database from 'better-sqlite3';
import { getDatabase } from '../database/connection.js';
import { LocalOpportunity, BatchStatus } from '../types/index.js';
import { calculateDistanceKm } from '../utils/distance.js';

export class OpportunityRepository {
  private db: Database.Database;

  constructor(customDb?: Database.Database) {
    this.db = customDb || getDatabase();
  }

  create(input: Omit<LocalOpportunity, 'id' | 'created_at'> & { id?: string }): LocalOpportunity {
    const id = input.id || `opp_${uuidv4()}`;
    const now = new Date().toISOString();

    const stmt = this.db.prepare(`
      INSERT INTO local_opportunities (
        id, qualification_id, centre_or_employer_name, type, district, block,
        address, latitude, longitude, batch_start_date, batch_end_date,
        total_seats, available_seats, sc_reserved_seats, batch_status,
        hostel_available, stipend_amount_inr, free_toolkit_provided, source,
        verified_by_worker_id, verified_at, created_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);

    stmt.run(
      id,
      input.qualification_id,
      input.centre_or_employer_name,
      input.type,
      input.district,
      input.block,
      input.address,
      input.latitude,
      input.longitude,
      input.batch_start_date,
      input.batch_end_date,
      input.total_seats,
      input.available_seats,
      input.sc_reserved_seats,
      input.batch_status,
      input.hostel_available ? 1 : 0,
      input.stipend_amount_inr,
      input.free_toolkit_provided ? 1 : 0,
      input.source,
      input.verified_by_worker_id || null,
      input.verified_at,
      now
    );

    return this.findById(id)!;
  }

  findById(id: string): LocalOpportunity | null {
    const stmt = this.db.prepare(`SELECT * FROM local_opportunities WHERE id = ?`);
    const row = stmt.get(id) as any;
    if (!row) return null;
    return this.mapRow(row);
  }

  listByQualification(qualificationId: string): LocalOpportunity[] {
    const stmt = this.db.prepare(`
      SELECT * FROM local_opportunities
      WHERE qualification_id = ?
      ORDER BY batch_start_date ASC
    `);
    const rows = stmt.all(qualificationId) as any[];
    return rows.map(this.mapRow);
  }

  list(filters?: {
    district?: string;
    block?: string;
    status?: BatchStatus;
    qualificationId?: string;
  }): LocalOpportunity[] {
    let query = `SELECT * FROM local_opportunities WHERE 1=1`;
    const params: any[] = [];

    if (filters?.district) {
      query += ` AND district = ?`;
      params.push(filters.district);
    }
    if (filters?.block) {
      query += ` AND block = ?`;
      params.push(filters.block);
    }
    if (filters?.status) {
      query += ` AND batch_status = ?`;
      params.push(filters.status);
    }
    if (filters?.qualificationId) {
      query += ` AND qualification_id = ?`;
      params.push(filters.qualificationId);
    }

    query += ` ORDER BY batch_start_date ASC`;

    const stmt = this.db.prepare(query);
    const rows = stmt.all(...params) as any[];
    return rows.map(this.mapRow);
  }

  /**
   * Find confirmed, active/upcoming batches for a qualification near a user's location
   */
  findLiveBatches(
    qualificationId: string,
    district: string,
    userLat: number,
    userLon: number,
    maxDistanceKm: number
  ): Array<LocalOpportunity & { distance_km: number }> {
    const stmt = this.db.prepare(`
      SELECT * FROM local_opportunities
      WHERE qualification_id = ?
        AND district = ?
        AND batch_status IN ('active', 'upcoming')
        AND available_seats > 0
    `);

    const rows = stmt.all(qualificationId, district) as any[];
    const results: Array<LocalOpportunity & { distance_km: number }> = [];

    for (const r of rows) {
      const opp = this.mapRow(r);
      const dist = calculateDistanceKm(userLat, userLon, opp.latitude, opp.longitude);
      // If within maxDistance or if hostel is available
      if (dist <= maxDistanceKm || opp.hostel_available) {
        results.push({ ...opp, distance_km: dist });
      }
    }

    return results.sort((a, b) => a.distance_km - b.distance_km);
  }

  updateBatchStatus(
    id: string,
    status: BatchStatus,
    workerId: string,
    availableSeats?: number
  ): LocalOpportunity | null {
    const opp = this.findById(id);
    if (!opp) return null;

    const now = new Date().toISOString();
    let query = `UPDATE local_opportunities SET batch_status = ?, verified_by_worker_id = ?, verified_at = ?`;
    const params: any[] = [status, workerId, now];

    if (availableSeats !== undefined) {
      query += `, available_seats = ?`;
      params.push(availableSeats);
    }

    query += ` WHERE id = ?`;
    params.push(id);

    const stmt = this.db.prepare(query);
    stmt.run(...params);

    return this.findById(id);
  }

  private mapRow(row: any): LocalOpportunity {
    return {
      id: row.id,
      qualification_id: row.qualification_id,
      centre_or_employer_name: row.centre_or_employer_name,
      type: row.type,
      district: row.district,
      block: row.block,
      address: row.address,
      latitude: row.latitude,
      longitude: row.longitude,
      batch_start_date: row.batch_start_date,
      batch_end_date: row.batch_end_date,
      total_seats: row.total_seats,
      available_seats: row.available_seats,
      sc_reserved_seats: row.sc_reserved_seats,
      batch_status: row.batch_status,
      hostel_available: Boolean(row.hostel_available),
      stipend_amount_inr: row.stipend_amount_inr,
      free_toolkit_provided: Boolean(row.free_toolkit_provided),
      source: row.source,
      verified_by_worker_id: row.verified_by_worker_id || undefined,
      verified_at: row.verified_at,
      created_at: row.created_at,
    };
  }
}
