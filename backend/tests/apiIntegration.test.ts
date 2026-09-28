import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import request from 'supertest';
import { createApp } from '../src/app.js';
import { getDatabase, closeDatabase } from '../src/database/connection.js';
import { runMigrations } from '../src/database/migrations.js';
import { seedDatabase } from '../src/database/seed.js';

describe('JeevanMitra 2.0 Backend End-to-End REST API Integration Suite', () => {
  let app: any;

  beforeAll(() => {
    // Run migrations and seed on database
    runMigrations();
    seedDatabase();
    app = createApp();
  });

  afterAll(() => {
    closeDatabase();
  });

  it('GET /api/health returns operational status and 6 AI layers active', async () => {
    const res = await request(app).get('/api/health');
    expect(res.status).toBe(200);
    expect(res.body.service).toContain('JeevanMitra 2.0');
    expect(res.body.database).toBe('healthy');
    expect(res.body.sixLayersStatus.layer1_intake).toBe('active');
    expect(res.body.sixLayersStatus.layer3_grounded_matching).toBe('active');
    expect(res.body.verifiedMatchProtocol).toBe('enforced');
  });

  it('full beneficiary lifecycle: Register -> DPDP Consent -> Voice Interview -> Profile Confirm -> Grounded Match', async () => {
    // 1. Register beneficiary
    const benRes = await request(app)
      .post('/api/beneficiaries')
      .send({
        name: 'Vikas SC Candidate',
        phone: '9811223344',
        gender: 'male',
        age: 22,
        category: 'SC',
        preferred_language: 'hi',
        district: 'Moradabad',
        block: 'Moradabad Rural',
      });
    expect(benRes.status).toBe(201);
    const benId = benRes.body.id;

    // 2. Record affirmative DPDP Act consent
    const cnsRes = await request(app)
      .post('/api/consents')
      .send({
        beneficiaryId: benId,
        purpose: 'PM-AJAY GIA Livelihood Matching',
        voiceRetentionChoice: 'do_not_keep',
        dpdpAffirmativeConsent: true,
      });
    expect(cnsRes.status).toBe(201);
    expect(cnsRes.body.consent.dpdp_affirmative_consent).toBe(true);

    // 3. Start Layer 1 Conversational Intake Interview
    const startRes = await request(app)
      .post('/api/interview/start')
      .send({
        beneficiaryId: benId,
        channel: 'web_app',
        language: 'hi',
      });
    expect(startRes.status).toBe(201);
    const sessionId = startRes.body.session.id;
    expect(startRes.body.firstQuestion.questionId).toBe('q1_location');

    // 4. Process an interview turn
    const turnRes = await request(app)
      .post('/api/interview/turn')
      .send({
        sessionId,
        speechOrText: 'Main Moradabad Rural se hoon aur 8th pass hoon',
      });
    expect(turnRes.status).toBe(200);
    expect(turnRes.body.currentQuestionIndex).toBe(1);

    // 5. Confirm beneficiary profile
    const confirmRes = await request(app)
      .post('/api/interview/confirm')
      .send({
        sessionId,
        beneficiaryId: benId,
        confirmedFields: {
          education_level: { value: 'Class 8', confidence: 0.95, confirmed: true },
          interests: { value: ['Electrical Systems', 'Domestic Wiring'], confidence: 0.92, confirmed: true },
          skills: { value: ['Basic Wiring'], confidence: 0.90, confirmed: true },
          mobility_radius_km: { value: 10, confidence: 0.95, confirmed: true },
          accessibility_needs: { value: 'None', confidence: 0.95, confirmed: true },
          work_preference: { value: 'both', confidence: 0.95, confirmed: true },
        },
      });
    expect(confirmRes.status).toBe(200);

    // 6. Run Layer 3 Grounded Matching
    const matchRes = await request(app)
      .post('/api/recommendations/match')
      .send({
        beneficiaryId: benId,
        sessionId,
      });
    expect(matchRes.status).toBe(200);
    expect(matchRes.body.recommendations.length).toBeGreaterThanOrEqual(1);

    const topRec = matchRes.body.recommendations[0];
    expect(topRec.score).toBeGreaterThan(60);
    // Since RSETI Electrician is in Moradabad Rural with open seats, it should be Verified Match
    expect(topRec.match_state).toBe('Verified Match');
  });

  it('field worker review & human-in-the-loop batch verification workflow', async () => {
    // 1. Get Cases
    const casesRes = await request(app).get('/api/worker/cases?district=Moradabad');
    expect(casesRes.status).toBe(200);
    expect(casesRes.body.cases.length).toBeGreaterThan(0);

    // 2. Fetch seeded beneficiary Amit Kumar (Bahjoi block with Interest Match only)
    const caseDetail = await request(app).get('/api/worker/cases/ben_amit_bahjoi');
    expect(caseDetail.status).toBe(200);
    expect(caseDetail.body.summary.threeLineBrief.length).toBe(3);

    // 3. Worker corrects profile (e.g. updates mobility radius)
    const patchRes = await request(app)
      .patch('/api/worker/cases/ben_amit_bahjoi/profile')
      .send({
        workerId: 'worker_vle_01',
        workerName: 'Ramesh Kumar (VLE)',
        corrections: {
          mobility_radius_km: '25',
        },
      });
    expect(patchRes.status).toBe(200);
    expect(patchRes.body.recommendations.length).toBeGreaterThan(0);
  });

  it('planning loop: supply-gap matrix and strictly grounded brief generation', async () => {
    // 1. Get Demand-Supply Matrix
    const matrixRes = await request(app).get('/api/planning/supply-gap-matrix?district=Moradabad');
    expect(matrixRes.status).toBe(200);
    expect(matrixRes.body.tradeDemandSupplyTable.length).toBeGreaterThan(0);

    // 2. Generate Layer 5 Narrative Brief
    const briefRes = await request(app)
      .post('/api/planning/generate-brief')
      .send({
        district: 'Moradabad',
        period: 'FY 2026-27 Q2',
      });
    expect(briefRes.status).toBe(201);
    expect(briefRes.body.brief.generated_narrative).toContain('Moradabad');
    const briefId = briefRes.body.brief.id;

    // 3. Sign-off brief by District Officer
    const signOffRes = await request(app)
      .post(`/api/planning/briefs/${briefId}/sign-off`)
      .send({
        officerName: 'Sanjay Sharma (District Welfare Officer)',
        status: 'signed_off',
      });
    expect(signOffRes.status).toBe(200);
    expect(signOffRes.body.brief.reviewer_sign_off_status).toBe('signed_off');

    // 4. Export perspective plan as CSV
    const exportRes = await request(app).get('/api/planning/export?district=Moradabad&format=csv');
    expect(exportRes.status).toBe(200);
    expect(exportRes.text).toContain('Trade Name');
    expect(exportRes.headers['content-type']).toContain('text/csv');
  });

  it('multi-channel endpoints: WhatsApp simulation and IVR simulation', async () => {
    // WhatsApp voice note simulation
    const waRes = await request(app)
      .post('/api/channels/whatsapp/simulate')
      .send({
        fromPhone: '9988776655',
        beneficiaryName: 'Ravi Kumar',
        voiceNoteTranscript: 'Humko gaon ke paas silai machine ka kaam seekhna hai',
        dialect: 'hi',
        district: 'Moradabad',
        block: 'Moradabad Rural',
      });
    expect(waRes.status).toBe(200);
    expect(waRes.body.channel).toBe('whatsapp');
    expect(waRes.body.outgoingBotResponse.actionPills.length).toBe(3);

    // IVR simulation
    const ivrRes = await request(app)
      .post('/api/channels/ivr/simulate')
      .send({
        callerNumber: '9988776655',
        currentStep: 1,
        dtmfDigit: '1',
      });
    expect(ivrRes.status).toBe(200);
    expect(ivrRes.body.channel).toBe('ivr');
    expect(ivrRes.body.twimlOrVoiceXml).toContain('<Response>');
  });

  it('immutable audit events verify state transitions and governance ledger', async () => {
    const auditRes = await request(app).get('/api/audit-events?limit=20');
    expect(auditRes.status).toBe(200);
    expect(auditRes.body.events.length).toBeGreaterThan(0);
  });
});
