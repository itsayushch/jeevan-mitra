import { Router, Request, Response } from 'express';
import { QualificationRepository } from '../repositories/qualificationRepository.js';
import { OpportunityRepository } from '../repositories/opportunityRepository.js';

const router = Router();
const qualRepo = new QualificationRepository();
const oppRepo = new OpportunityRepository();

router.get('/qualifications', (req: Request, res: Response) => {
  const { sector } = req.query;
  const list = sector ? qualRepo.listBySector(String(sector)) : qualRepo.listVerified();
  res.json({
    count: list.length,
    qualifications: list,
  });
});

router.get('/qualifications/:id', (req: Request, res: Response) => {
  const id = String(req.params.id);
  const qual = qualRepo.findById(id);
  if (!qual) {
    res.status(404).json({ error: 'Qualification not found' });
    return;
  }
  const opps = oppRepo.listByQualification(id);
  res.json({
    qualification: qual,
    activeBatches: opps,
  });
});

router.get('/opportunities', (req: Request, res: Response) => {
  const { district, block, status } = req.query;
  const opps = oppRepo.list({
    district: district ? String(district) : undefined,
    block: block ? String(block) : undefined,
    status: status as any,
  });
  res.json({
    count: opps.length,
    opportunities: opps,
  });
});

export default router;
