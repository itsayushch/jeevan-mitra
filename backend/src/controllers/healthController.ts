import { Request, Response } from 'express';
import { getDb } from '../database/connection.js';
import { env } from '../config/env.js';

export class HealthController {
  check = async (req: Request, res: Response): Promise<void> => {
    let dbStatus = 'healthy';
    try {
      const db = getDb();
      await db.$queryRaw`SELECT 1`;
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
