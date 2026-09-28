import { Request, Response } from 'express';
import { z } from 'zod';
import { BeneficiaryRepository } from '../repositories/beneficiaryRepository.js';
import { ConsentRepository } from '../repositories/consentRepository.js';

export const createBeneficiarySchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  phone: z.string().optional(),
  gender: z.enum(['male', 'female', 'other', 'prefer_not_to_say']).default('prefer_not_to_say'),
  age: z.number().int().min(14).max(65).optional(),
  category: z.string().default('SC'),
  preferred_language: z.enum(['hi', 'bho', 'awa', 'en', 'bn', 'ta', 'te']).default('hi'),
  district: z.string().default('Moradabad'),
  block: z.string().default('Moradabad Rural'),
  village: z.string().optional(),
  contact_preference: z.enum(['voice', 'whatsapp', 'sms', 'field_worker']).default('voice'),
});

export class BeneficiaryController {
  private beneficiaryRepo: BeneficiaryRepository;
  private consentRepo: ConsentRepository;

  constructor() {
    this.beneficiaryRepo = new BeneficiaryRepository();
    this.consentRepo = new ConsentRepository();
  }

  create = (req: Request, res: Response): void => {
    const data = createBeneficiarySchema.parse(req.body);
    const beneficiary = this.beneficiaryRepo.create(data);
    res.status(201).json(beneficiary);
  };

  getById = (req: Request, res: Response): void => {
    const id = String(req.params.id);
    const beneficiary = this.beneficiaryRepo.findById(id);
    if (!beneficiary) {
      res.status(404).json({ error: 'Beneficiary not found' });
      return;
    }

    const consents = this.consentRepo.getByBeneficiaryId(id);
    res.json({
      ...beneficiary,
      consents,
    });
  };

  list = (req: Request, res: Response): void => {
    const { district, block, limit } = req.query;
    const beneficiaries = this.beneficiaryRepo.list({
      district: district ? String(district) : undefined,
      block: block ? String(block) : undefined,
      limit: limit ? Number(limit) : undefined,
    });
    res.json({
      count: beneficiaries.length,
      beneficiaries,
    });
  };

  update = (req: Request, res: Response): void => {
    const id = String(req.params.id);
    const updated = this.beneficiaryRepo.update(id, req.body);
    if (!updated) {
      res.status(404).json({ error: 'Beneficiary not found' });
      return;
    }
    res.json(updated);
  };
}
