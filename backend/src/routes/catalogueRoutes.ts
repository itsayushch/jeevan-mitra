import { Router, Request, Response, NextFunction } from 'express';
import { QualificationRepository } from '../repositories/qualificationRepository.js';
import { OpportunityRepository } from '../repositories/opportunityRepository.js';

const router = Router();
const qualRepo = new QualificationRepository();
const oppRepo = new OpportunityRepository();

router.get('/qualifications', async (req: Request, res: Response, next: NextFunction): Promise<void> => {
  try {
    const { sector } = req.query;
    const list = sector ? await qualRepo.listBySector(String(sector)) : await qualRepo.listVerified();
    res.json({
      count: list.length,
      qualifications: list,
    });
  } catch (err) {
    next(err);
  }
});

router.get('/qualifications/:id', async (req: Request, res: Response, next: NextFunction): Promise<void> => {
  try {
    const id = String(req.params.id);
    const qual = await qualRepo.findById(id);
    if (!qual) {
      res.status(404).json({ error: 'Qualification not found' });
      return;
    }
    const opps = await oppRepo.listByQualification(id);
    res.json({
      qualification: qual,
      activeBatches: opps,
    });
  } catch (err) {
    next(err);
  }
});

router.get('/opportunities', async (req: Request, res: Response, next: NextFunction): Promise<void> => {
  try {
    const { district, block, status } = req.query;
    const opps = await oppRepo.list({
      district: district ? String(district) : undefined,
      block: block ? String(block) : undefined,
      status: status as any,
    });
    res.json({
      count: opps.length,
      opportunities: opps,
    });
  } catch (err) {
    next(err);
  }
});

export default router;
