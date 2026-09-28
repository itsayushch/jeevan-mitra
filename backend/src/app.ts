import express, { Express, Request, Response } from 'express';
import cors from 'cors';
import apiRouter from './routes/index.js';
import { errorHandler } from './middleware/errorHandler.js';

export function createApp(): Express {
  const app = express();

  app.use(cors());
  app.use(express.json({ limit: '10mb' }));
  app.use(express.urlencoded({ extended: true }));

  // Root Welcome / Documentation Endpoint
  app.get('/', (req: Request, res: Response) => {
    res.json({
      name: 'JeevanMitra 2.0 Backend Core API',
      version: '2.0.0',
      description:
        'A Verification-First, Multi-Layer Generative AI System for PM-AJAY Livelihood Matching & District Planning',
      ministry: 'Ministry of Social Justice & Empowerment (MoSJE)',
      scheme: 'PM-AJAY (Grant-in-Aid Component)',
      problemStatementId: '26097',
      endpoints: {
        health: '/api/health',
        beneficiaries: '/api/beneficiaries',
        consent: '/api/consents',
        interview_layer1_2: '/api/interview',
        recommendations_layer3: '/api/recommendations',
        field_worker_layer4: '/api/worker',
        referrals_outcomes: '/api/referrals',
        planning_briefs_layer5: '/api/planning',
        drift_monitoring_layer6: '/api/monitoring',
        channels_whatsapp_ivr: '/api/channels',
        audit_ledger: '/api/audit-events',
        nqr_catalogue: '/api/catalogue/qualifications',
      },
      keyGuarantees: [
        'Claim 1: The Verified Match Protocol with hard data-layer invariants',
        'Claim 2: Grounded Planning Loop directly feeding Annual Action Plans (AAPs)',
        'Six isolated accountable Generative AI layers with strict guardrails',
        'DPDP Act notice & affirmative consent compliance',
      ],
    });
  });

  // Master API router
  app.use('/api', apiRouter);

  // Centralized Error Handler
  app.use(errorHandler);

  return app;
}
