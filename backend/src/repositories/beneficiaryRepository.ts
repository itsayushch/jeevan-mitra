import { v4 as uuidv4 } from 'uuid';
import { PrismaClient } from '@prisma/client';
import { getDb } from '../database/connection.js';
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
  private prisma: PrismaClient;

  constructor(customPrisma?: PrismaClient) {
    this.prisma = customPrisma || getDb();
  }

  async create(input: CreateBeneficiaryInput): Promise<Beneficiary> {
    const id = input.id || `ben_${uuidv4()}`;

    const ben = await this.prisma.beneficiary.create({
      data: {
        id,
        name: input.name,
        phone: input.phone || null,
        gender: input.gender || 'prefer_not_to_say',
        age: input.age || null,
        category: input.category || 'SC',
        preferred_language: input.preferred_language || 'hi',
        district: input.district,
        block: input.block,
        village: input.village || null,
        contact_preference: input.contact_preference || 'voice',
      },
    });

    return this.mapRow(ben);
  }

  async findById(id: string): Promise<Beneficiary | null> {
    const row = await this.prisma.beneficiary.findUnique({ where: { id } });
    if (!row) return null;
    return this.mapRow(row);
  }

  async findByPhone(phone: string): Promise<Beneficiary | null> {
    const row = await this.prisma.beneficiary.findFirst({ where: { phone } });
    if (!row) return null;
    return this.mapRow(row);
  }

  async list(filters?: { district?: string; block?: string; limit?: number }): Promise<Beneficiary[]> {
    const where: any = {};
    if (filters?.district) where.district = filters.district;
    if (filters?.block) where.block = filters.block;

    const rows = await this.prisma.beneficiary.findMany({
      where,
      orderBy: { created_at: 'desc' },
      take: filters?.limit,
    });

    return rows.map(this.mapRow);
  }

  async update(id: string, updates: Partial<CreateBeneficiaryInput>): Promise<Beneficiary | null> {
    const existing = await this.findById(id);
    if (!existing) return null;

    const row = await this.prisma.beneficiary.update({
      where: { id },
      data: {
        name: updates.name,
        phone: updates.phone,
        gender: updates.gender,
        age: updates.age,
        category: updates.category,
        preferred_language: updates.preferred_language,
        district: updates.district,
        block: updates.block,
        village: updates.village,
        contact_preference: updates.contact_preference,
      },
    });

    return this.mapRow(row);
  }

  private mapRow(row: any): Beneficiary {
    return {
      id: row.id,
      name: row.name,
      phone: row.phone || undefined,
      gender: row.gender,
      age: row.age || undefined,
      category: row.category,
      preferred_language: row.preferred_language as LanguageCode,
      district: row.district,
      block: row.block,
      village: row.village || undefined,
      contact_preference: row.contact_preference,
      created_at: row.created_at.toISOString(),
      updated_at: row.updated_at.toISOString(),
    };
  }
}
