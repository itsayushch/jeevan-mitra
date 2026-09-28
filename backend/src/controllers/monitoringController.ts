import { Request, Response } from 'express';
import { z } from 'zod';
import { AdvisoryQueueManager } from '../ai-layers/layer6-monitoring/advisoryQueue.js';

export const updateAdvisorySchema = z.object({
  status: z.enum(['acknowledged', 'resolved']),
});

export const auditDriftSchema = z.object({
  district: z.string().optional().default('Moradabad'),
});

export class MonitoringController {
  private queueManager: AdvisoryQueueManager;

  constructor() {
    this.queueManager = new AdvisoryQueueManager();
  }

  auditDrift = async (req: Request, res: Response, next: any): Promise<void> => {
    try {
      const { district } = auditDriftSchema.parse(req.body);
      const advisories = await this.queueManager.runAuditCycle(district);

      res.json({
        district,
        auditTimestamp: new Date().toISOString(),
        advisoriesGenerated: advisories.length,
        advisories,
      });
    } catch (err) {
      next(err);
    }
  };

  getAdvisories = async (req: Request, res: Response, next: any): Promise<void> => {
    try {
      const district = req.query.district ? String(req.query.district) : undefined;
      const list = await this.queueManager.getReviewerQueue(district);
      res.json({
        count: list.length,
        advisories: list,
      });
    } catch (err) {
      next(err);
    }
  };

  updateAdvisory = async (req: Request, res: Response, next: any): Promise<void> => {
    try {
      const id = String(req.params.id);
      const { status } = updateAdvisorySchema.parse(req.body);

      const success = await (status === 'acknowledged'
        ? this.queueManager.acknowledgeAdvisory(id)
        : this.queueManager.resolveAdvisory(id));

      if (!success) {
        res.status(404).json({ error: 'Advisory not found' });
        return;
      }

      res.json({ message: `Advisory updated to status '${status}'.` });
    } catch (err) {
      next(err);
    }
  };
}
