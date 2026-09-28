import { v4 as uuidv4 } from 'uuid';
import { PrismaClient } from '@prisma/client';
import { getDb } from '../database/connection.js';
import { LocalOpportunity, BatchStatus } from '../types/index.js';
import { calculateDistanceKm } from '../utils/distance.js';

export class OpportunityRepository {
  private prisma: PrismaClient;

  constructor(customPrisma?: PrismaClient) {
    this.prisma = customPrisma || getDb();
  }

  async create(input: Omit<LocalOpportunity, 'id' | 'created_at'> & { id?: string }): Promise<LocalOpportunity> {
    const id = input.id || `opp_${uuidv4()}`;

    const opp = await this.prisma.localOpportunity.create({
      data: {
        id,
        qualification_id: input.qualification_id,
        centre_or_employer_name: input.centre_or_employer_name,
        type: input.type,
        district: input.district,
        block: input.block,
        address: input.address,
        latitude: input.latitude,
        longitude: input.longitude,
        batch_start_date: new Date(input.batch_start_date),
        batch_end_date: new Date(input.batch_end_date),
        total_seats: input.total_seats,
        available_seats: input.available_seats,
        sc_reserved_seats: input.sc_reserved_seats,
        batch_status: input.batch_status,
        hostel_available: input.hostel_available,
        stipend_amount_inr: input.stipend_amount_inr,
        free_toolkit_provided: input.free_toolkit_provided,
        source: input.source,
        verified_by_worker_id: input.verified_by_worker_id || null,
        verified_at: new Date(input.verified_at),
      },
    });

    return this.mapRow(opp);
  }

  async findById(id: string): Promise<LocalOpportunity | null> {
    const row = await this.prisma.localOpportunity.findUnique({ where: { id } });
    if (!row) return null;
    return this.mapRow(row);
  }

  async listByQualification(qualificationId: string): Promise<LocalOpportunity[]> {
    const rows = await this.prisma.localOpportunity.findMany({
      where: { qualification_id: qualificationId },
      orderBy: { batch_start_date: 'asc' },
    });
    return rows.map(this.mapRow);
  }

  async list(filters?: {
    district?: string;
    block?: string;
    status?: BatchStatus;
    qualificationId?: string;
  }): Promise<LocalOpportunity[]> {
    const where: any = {};
    if (filters?.district) where.district = filters.district;
    if (filters?.block) where.block = filters.block;
    if (filters?.status) where.batch_status = filters.status;
    if (filters?.qualificationId) where.qualification_id = filters.qualificationId;

    const rows = await this.prisma.localOpportunity.findMany({
      where,
      orderBy: { batch_start_date: 'asc' },
    });
    return rows.map(this.mapRow);
  }

  async findLiveBatches(
    qualificationId: string,
    district: string,
    userLat: number,
    userLon: number,
    maxDistanceKm: number
  ): Promise<Array<LocalOpportunity & { distance_km: number }>> {
    const rows = await this.prisma.localOpportunity.findMany({
      where: {
        qualification_id: qualificationId,
        district: district,
        batch_status: { in: ['active', 'upcoming'] },
        available_seats: { gt: 0 },
      },
    });

    const results: Array<LocalOpportunity & { distance_km: number }> = [];

    for (const r of rows) {
      const opp = this.mapRow(r);
      const dist = calculateDistanceKm(userLat, userLon, opp.latitude, opp.longitude);
      if (dist <= maxDistanceKm || opp.hostel_available) {
        results.push({ ...opp, distance_km: dist });
      }
    }

    return results.sort((a, b) => a.distance_km - b.distance_km);
  }

  async updateBatchStatus(
    id: string,
    status: BatchStatus,
    workerId: string,
    availableSeats?: number
  ): Promise<LocalOpportunity | null> {
    const opp = await this.findById(id);
    if (!opp) return null;

    const data: any = {
      batch_status: status,
      verified_by_worker_id: workerId,
      verified_at: new Date(),
    };

    if (availableSeats !== undefined) {
      data.available_seats = availableSeats;
    }

    const row = await this.prisma.localOpportunity.update({
      where: { id },
      data,
    });

    return this.mapRow(row);
  }

  private mapRow(row: any): LocalOpportunity {
    return {
      id: row.id,
      qualification_id: row.qualification_id,
      centre_or_employer_name: row.centre_or_employer_name,
      type: row.type as any,
      district: row.district,
      block: row.block,
      address: row.address,
      latitude: row.latitude,
      longitude: row.longitude,
      batch_start_date: row.batch_start_date.toISOString(),
      batch_end_date: row.batch_end_date.toISOString(),
      total_seats: row.total_seats,
      available_seats: row.available_seats,
      sc_reserved_seats: row.sc_reserved_seats,
      batch_status: row.batch_status as any,
      hostel_available: row.hostel_available,
      stipend_amount_inr: row.stipend_amount_inr,
      free_toolkit_provided: row.free_toolkit_provided,
      source: row.source,
      verified_by_worker_id: row.verified_by_worker_id || undefined,
      verified_at: row.verified_at.toISOString(),
      created_at: row.created_at.toISOString(),
    };
  }
}
