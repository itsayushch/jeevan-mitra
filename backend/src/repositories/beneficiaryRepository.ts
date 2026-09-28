import { v4 as uuidv4 } from 'uuid';
import Database from 'better-sqlite3';
import { getDatabase } from '../database/connection.js';
import { Beneficiary, LanguageCode } from '../types/index.js';

export interface CreateBeneficiaryInput {
  id?: string;
  name: string;
  phone?: string;
  gender?: 'male' | 'female' | 'other' | 'prefer_not_to_say';
  age?: number;
  category?: string;
  preferred_language?: LanguageCode;
  district: string;
  block: string;
  village?: string;
  contact_preference?: 'voice' | 'whatsapp' | 'sms' | 'field_worker';
}

export class BeneficiaryRepository {
  private db: Database.Database;

  constructor(customDb?: Database.Database) {
    this.db = customDb || getDatabase();
  }

  create(input: CreateBeneficiaryInput): Beneficiary {
    const id = input.id || `ben_${uuidv4()}`;
    const now = new Date().toISOString();

    const stmt = this.db.prepare(`
      INSERT INTO beneficiaries (
        id, name, phone, gender, age, category, preferred_language,
        district, block, village, contact_preference, created_at, updated_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);

    stmt.run(
      id,
      input.name,
      input.phone || null,
      input.gender || 'prefer_not_to_say',
      input.age || null,
      input.category || 'SC',
      input.preferred_language || 'hi',
      input.district,
      input.block,
      input.village || null,
      input.contact_preference || 'voice',
      now,
      now
    );

    return this.findById(id)!;
  }

  findById(id: string): Beneficiary | null {
    const stmt = this.db.prepare(`SELECT * FROM beneficiaries WHERE id = ?`);
    const row = stmt.get(id) as any;
    if (!row) return null;
    return this.mapRow(row);
  }

  findByPhone(phone: string): Beneficiary | null {
    const stmt = this.db.prepare(`SELECT * FROM beneficiaries WHERE phone = ?`);
    const row = stmt.get(phone) as any;
    if (!row) return null;
    return this.mapRow(row);
  }

  list(filters?: { district?: string; block?: string; limit?: number }): Beneficiary[] {
    let query = `SELECT * FROM beneficiaries WHERE 1=1`;
    const params: any[] = [];

    if (filters?.district) {
      query += ` AND district = ?`;
      params.push(filters.district);
    }
    if (filters?.block) {
      query += ` AND block = ?`;
      params.push(filters.block);
    }

    query += ` ORDER BY created_at DESC`;

    if (filters?.limit) {
      query += ` LIMIT ?`;
      params.push(filters.limit);
    }

    const stmt = this.db.prepare(query);
    const rows = stmt.all(...params) as any[];
    return rows.map(this.mapRow);
  }

  update(id: string, updates: Partial<CreateBeneficiaryInput>): Beneficiary | null {
    const existing = this.findById(id);
    if (!existing) return null;

    const now = new Date().toISOString();
    const updated = { ...existing, ...updates, updated_at: now };

    const stmt = this.db.prepare(`
      UPDATE beneficiaries
      SET name = ?, phone = ?, gender = ?, age = ?, category = ?,
          preferred_language = ?, district = ?, block = ?, village = ?,
          contact_preference = ?, updated_at = ?
      WHERE id = ?
    `);

    stmt.run(
      updated.name,
      updated.phone || null,
      updated.gender,
      updated.age || null,
      updated.category,
      updated.preferred_language,
      updated.district,
      updated.block,
      updated.village || null,
      updated.contact_preference,
      now,
      id
    );

    return this.findById(id);
  }

  private mapRow(row: any): Beneficiary {
    return {
      id: row.id,
      name: row.name,
      phone: row.phone || undefined,
      gender: row.gender,
      age: row.age || undefined,
      category: row.category,
      preferred_language: row.preferred_language,
      district: row.district,
      block: row.block,
      village: row.village || undefined,
      contact_preference: row.contact_preference,
      created_at: row.created_at,
      updated_at: row.updated_at,
    };
  }
}
