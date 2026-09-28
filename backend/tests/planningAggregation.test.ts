import { describe, it, expect, beforeEach } from 'vitest';
import { PlanningAggregationService } from '../src/ai-layers/layer5-planning/aggregationService.js';
import { PlanningNarrativeEngine } from '../src/ai-layers/layer5-planning/narrativeEngine.js';

describe('Claim 2 & Layer 5: Planning Loop & Strictly Grounded Narrative Tests', () => {
  let aggregationService: PlanningAggregationService;
  let narrativeEngine: PlanningNarrativeEngine;

  beforeEach(() => {
    const mockPlanningRepo: any = {
      getDemandSupplyMatrix: async (district: string) => ({
        totalBeneficiaries: 15,
        totalVerifiedMatches: 0,
        totalGaps: 15,
        gaps: [
          {
            trade_name: 'Micro-Irrigation Technician',
            nqr_code: 'AGR/Q1003',
            sector: 'Agriculture',
            voice_demand: 15,
            sanctioned_seats: 0,
            active_batches: 0,
            supply_gap: 15,
            gap_status: 'No Centre',
            block_breakdown: { Bahjoi: { demand: 15, capacity: 0 } },
          },
        ],
        clusterAlerts: [
          {
            block: 'Bahjoi',
            trade: 'Micro-Irrigation Technician',
            demand: 15,
            nearest_centre_distance_km: 45,
            suggested_action: 'Arrange transport stipend / bus pass to nearest district ITI',
          },
        ],
      }),
    };

    aggregationService = new PlanningAggregationService(mockPlanningRepo);
    narrativeEngine = new PlanningNarrativeEngine();
  });

  it('accurately calculates voice demand versus sanctioned capacity without errors', async () => {
    const summary = await aggregationService.aggregateDemandVsCapacity('Moradabad');

    expect(summary.totalBeneficiaries).toBe(15);
    expect(summary.totalVerifiedMatches).toBe(0);
    expect(summary.totalSupplyGaps).toBe(15);

    const irrigGap = summary.gaps.find((g) => g.nqr_code === 'AGR/Q1003');
    expect(irrigGap).toBeDefined();
    expect(irrigGap?.voice_demand).toBe(15);
    expect(irrigGap?.sanctioned_seats).toBe(0);
    expect(irrigGap?.gap_status).toBe('No Centre');
    expect(irrigGap?.supply_gap).toBe(15);
  });

  it('guarantees Layer 5 strictly grounds all numbers from database query results in narrative text', async () => {
    const summary = await aggregationService.aggregateDemandVsCapacity('Moradabad');
    const brief = narrativeEngine.generateBrief(summary, 'FY 2026-27 Q2');

    // Strict numerical assertions: narrative MUST contain the exact database numbers
    expect(brief.narrativeText).toContain('15 SC youth');
    expect(brief.narrativeText).toContain('0 candidates were successfully matched');
    expect(brief.narrativeText).toContain('unmet demand gap of 15 candidate allocations');
    expect(brief.narrativeText).toContain('Micro-Irrigation Technician');
    expect(brief.narrativeText).toContain('recorded 15 voice requests against 0 sanctioned seats');

    // Check cluster alert
    expect(brief.narrativeText).toContain('Block Bahjoi');
    expect(brief.narrativeText).toContain('nearest sanctioned centre is approximately 45 km away');

    // Traceability metadata check
    expect(brief.sourceDataTrace.totalInterviewed).toBe(15);
    expect(brief.sourceDataTrace.unmetDemand).toBe(15);
  });
});
