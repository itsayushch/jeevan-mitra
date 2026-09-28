import { Router, Request, Response } from 'express';
import { AuditRepository } from '../repositories/auditRepository.js';

const router = Router();
const auditRepo = new AuditRepository();

router.get('/', (req: Request, res: Response) => {
  const limit = req.query.limit ? Number(req.query.limit) : 50;
  const events = auditRepo.getRecentEvents(limit);
  res.json({
    count: events.length,
    events,
  });
});

router.get('/entity/:entityType/:entityId', (req: Request, res: Response) => {
  const entityType = String(req.params.entityType);
  const entityId = String(req.params.entityId);
  const events = auditRepo.getEventsByEntity(entityType, entityId);
  res.json({
    entityType,
    entityId,
    count: events.length,
    events,
  });
});

export default router;
