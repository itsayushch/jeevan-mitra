import { PrismaClient } from '@prisma/client';
import { getDb } from '../database/connection.js';
import { Qualification } from '../types/index.js';

export class QualificationRepository {
  private prisma: PrismaClient;

  constructor(customPrisma?: PrismaClient) {
    this.prisma = customPrisma || getDb();
  }

  async create(input: Qualification): Promise<Qualification> {
    const qual = await this.prisma.qualification.create({
      data: {
        id: input.id,
        nqr_code: input.nqr_code,
        title: input.title,
        sector: input.sector,
        nsqf_level: input.nsqf_level,
        duration_hours: input.duration_hours,
        min_education: input.min_education,
        min_education_rank: input.min_education_rank,
        work_type: input.work_type,
        physical_intensity: input.physical_intensity || 'light',
        skills_acquired: JSON.stringify(input.skills_acquired),
        curriculum_summary: input.curriculum_summary,
        entry_criteria: input.entry_criteria,
        certification_body: input.certification_body,
        nqr_link: input.nqr_link,
        verification_status: input.verification_status || 'verified',
        verification_date: new Date(input.verification_date),
      },
    });

    return this.mapRow(qual);
  }

  async findById(id: string): Promise<Qualification | null> {
    const row = await this.prisma.qualification.findUnique({ where: { id } });
    if (!row) return null;
    return this.mapRow(row);
  }

  async findByNqrCode(code: string): Promise<Qualification | null> {
    const row = await this.prisma.qualification.findUnique({ where: { nqr_code: code } });
    if (!row) return null;
    return this.mapRow(row);
  }

  async listVerified(): Promise<Qualification[]> {
    const rows = await this.prisma.qualification.findMany({
      where: { verification_status: 'verified' },
      orderBy: [
        { nsqf_level: 'asc' },
        { title: 'asc' }
      ]
    });
    return rows.map(this.mapRow);
  }

  async listBySector(sector: string): Promise<Qualification[]> {
    const rows = await this.prisma.qualification.findMany({
      where: { 
        sector,
        verification_status: 'verified'
      },
      orderBy: { nsqf_level: 'asc' }
    });
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
      work_type: row.work_type as any,
      physical_intensity: row.physical_intensity as any,
      skills_acquired: JSON.parse(row.skills_acquired || '[]'),
      curriculum_summary: row.curriculum_summary,
      entry_criteria: row.entry_criteria,
      certification_body: row.certification_body,
      nqr_link: row.nqr_link,
      verification_status: row.verification_status as any,
      verification_date: row.verification_date.toISOString(),
    };
  }
}
