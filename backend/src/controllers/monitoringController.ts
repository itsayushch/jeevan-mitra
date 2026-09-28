import { Request, Response } from 'express';
import { z } from 'zod';
import { AdvisoryQueueManager } from '../ai-layers/layer6-monitoring/advisoryQueue.js';

export const updateAdvisorySchema = z.object({
  status: z.enum(['acknowledged', 'resolved']),
});

export class MonitoringController {
  private queueManager: AdvisoryQueueManager;

  constructor() {
    this.queueManager = new AdvisoryQueueManager();
  }

  auditDrift = (req: Request, res: Response): void => {
    const district = (req.body.district as string) || 'Moradabad';
    const advisories = this.queueManager.runAuditCycle(district);

    res.json({
      district,
      auditTimestamp: new Date().toISOString(),
      advisoriesGenerated: advisories.length,
      advisories,
    });
  };

  getAdvisories = (req: Request, res: Response): void => {
    const district = req.query.district ? String(req.query.district) : undefined;
    const list = this.queueManager.getReviewerQueue(district);
    res.json({
      count: list.length,
      advisories: list,
    });
  };

  updateAdvisory = (req: Request, res: Response): void => {
    const id = String(req.params.id);
    const { status } = updateAdvisorySchema.parse(req.body);

    const success =
      status === 'acknowledged'
        ? this.queueManager.acknowledgeAdvisory(id)
        : this.queueManager.resolveAdvisory(id);

    if (!success) {
      res.status(404).json({ error: 'Advisory not found' });
      return;
    }

    res.json({ message: `Advisory updated to status '${status}'.` });
  };
}
