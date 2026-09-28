import { Router, Request, Response, NextFunction } from 'express';
import { AuditRepository } from '../repositories/auditRepository.js';
import { z } from 'zod';

const router = Router();
const auditRepo = new AuditRepository();

const getRecentEventsSchema = z.object({
  limit: z.coerce.number().optional().default(50),
});

router.get('/', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const { limit } = getRecentEventsSchema.parse(req.query);
    const events = await auditRepo.getRecentEvents(limit);
    res.json({
      count: events.length,
      events,
    });
  } catch (err) {
    next(err);
  }
});

router.get('/entity/:entityType/:entityId', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const entityType = String(req.params.entityType);
    const entityId = String(req.params.entityId);
    const events = await auditRepo.getEventsByEntity(entityType, entityId);
    res.json({
      entityType,
      entityId,
      count: events.length,
      events,
    });
  } catch (err) {
    next(err);
  }
});

export default router;
