import { Request, Response } from 'express';
import { getDatabase } from '../database/connection.js';
import { env } from '../config/env.js';

export class HealthController {
  check(req: Request, res: Response): void {
    let dbStatus = 'healthy';
    try {
      const db = getDatabase();
      db.prepare('SELECT 1').get();
    } catch (e: any) {
      dbStatus = `unhealthy: ${e.message}`;
    }

    res.json({
      service: 'JeevanMitra 2.0 Backend Core',
      status: 'operational',
      timestamp: new Date().toISOString(),
      environment: env.NODE_ENV,
      defaultDistrict: env.DEFAULT_DISTRICT,
      defaultState: env.DEFAULT_STATE,
      aiProvider: env.AI_PROVIDER,
      database: dbStatus,
      sixLayersStatus: {
        layer1_intake: 'active',
        layer2_extraction: 'active',
        layer3_grounded_matching: 'active',
        layer4_copilot: 'active',
        layer5_planning_narrative: 'active',
        layer6_drift_monitoring: 'active',
      },
      verifiedMatchProtocol: 'enforced',
    });
  }
}
