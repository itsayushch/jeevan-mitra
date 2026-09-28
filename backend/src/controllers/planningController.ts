import { Request, Response } from 'express';
import { z } from 'zod';
import { PlanningAggregationService } from '../ai-layers/layer5-planning/aggregationService.js';
import { PlanningNarrativeEngine } from '../ai-layers/layer5-planning/narrativeEngine.js';
import { PlanningRepository } from '../repositories/planningRepository.js';

export const generateBriefSchema = z.object({
  district: z.string().default('Moradabad'),
  period: z.string().default('FY 2026-27 Q2'),
});

export const signOffSchema = z.object({
  officerName: z.string().min(2),
  status: z.enum(['signed_off', 'rejected']).default('signed_off'),
});

export class PlanningController {
  private aggregationService: PlanningAggregationService;
  private narrativeEngine: PlanningNarrativeEngine;
  private planningRepo: PlanningRepository;

  constructor() {
    this.planningRepo = new PlanningRepository();
    this.aggregationService = new PlanningAggregationService(this.planningRepo);
    this.narrativeEngine = new PlanningNarrativeEngine();
  }

  /**
   * Screen 12: District GIA perspective planning dashboard
   */
  getDemandSupplyMatrix = async (req: Request, res: Response, next: any): Promise<void> => {
    try {
      const district = (req.query.district as string) || 'Moradabad';
      const summary = await this.aggregationService.aggregateDemandVsCapacity(district);

      res.json({
        district: summary.district,
        fiscalYear: 'FY 2026-27',
        metrics: {
          beneficiariesInterviewed: summary.totalBeneficiaries,
          verifiedMatches: summary.totalVerifiedMatches,
          unmetDemandGaps: summary.totalSupplyGaps,
        },
        tradeDemandSupplyTable: summary.gaps.map((g) => ({
          tradeName: g.trade_name,
          nqrCode: g.nqr_code,
          sector: g.sector,
          voiceDemand: g.voice_demand,
          sanctionedSeats: g.sanctioned_seats,
          supplyGap: -g.supply_gap,
          status: `${g.gap_status}`,
        })),
        geographicClusterAlerts: summary.clusterAlerts.map((a) => ({
          alert: `Block ${a.block}: ${a.demand} SC youth requested ${a.trade}; nearest centre ${a.nearest_centre_distance_km}km`,
          recommendation: a.suggested_action,
        })),
      });
    } catch (err) {
      next(err);
    }
  };

  /**
   * Layer 5 Planning Narrative Generator
   */
  generateBrief = async (req: Request, res: Response, next: any): Promise<void> => {
    try {
      const data = generateBriefSchema.parse(req.body);
      const summary = await this.aggregationService.aggregateDemandVsCapacity(data.district);
      const generated = this.narrativeEngine.generateBrief(summary, data.period);

      const saved = await this.planningRepo.saveBrief({
        district: data.district,
        period: data.period,
        totalBeneficiaries: summary.totalBeneficiaries,
        totalVerifiedMatches: summary.totalVerifiedMatches,
        totalSupplyGaps: summary.totalSupplyGaps,
        aggregationSnapshot: {
          gaps: summary.gaps,
          cluster_alerts: summary.clusterAlerts,
          generated_at: new Date().toISOString(),
        },
        generatedNarrative: generated.narrativeText,
        suggestedPolicyActions: generated.suggestedPolicyActions,
      });

      res.status(201).json({
        brief: saved,
        insights: generated.keyInsights,
        sourceDataTrace: generated.sourceDataTrace,
      });
    } catch (err) {
      next(err);
    }
  };

  listBriefs = async (req: Request, res: Response, next: any): Promise<void> => {
    try {
      const district = req.query.district ? String(req.query.district) : undefined;
      const briefs = await this.planningRepo.listBriefs(district);
      res.json({
        count: briefs.length,
        briefs,
      });
    } catch (err) {
      next(err);
    }
  };

  getBriefById = async (req: Request, res: Response, next: any): Promise<void> => {
    try {
      const id = String(req.params.id);
      const brief = await this.planningRepo.getBriefById(id);
      if (!brief) {
        res.status(404).json({ error: 'Planning brief not found' });
        return;
      }
      res.json(brief);
    } catch (err) {
      next(err);
    }
  };

  signOff = async (req: Request, res: Response, next: any): Promise<void> => {
    try {
      const id = String(req.params.id);
      const data = signOffSchema.parse(req.body);

      const updated = await this.planningRepo.signOffBrief(id, data.officerName, data.status);
      if (!updated) {
        res.status(404).json({ error: 'Planning brief not found' });
        return;
      }

      res.json({
        message: `Planning brief successfully signed off by District Officer ${data.officerName}. Ready for Annual Action Plan (AAP) submission.`,
        brief: updated,
      });
    } catch (err) {
      next(err);
    }
  };

  /**
   * Export Perspective Plan as CSV or JSON
   */
  exportPlan = async (req: Request, res: Response, next: any): Promise<void> => {
    try {
      const district = (req.query.district as string) || 'Moradabad';
      const format = (req.query.format as string) || 'csv';
      const summary = await this.aggregationService.aggregateDemandVsCapacity(district);

      if (format === 'csv') {
        let csv = 'Trade Name,NQR Code,Sector,Voice Demand,Sanctioned Seats,Supply Gap,Status\n';
        for (const g of summary.gaps) {
          csv += `"${g.trade_name}","${g.nqr_code}","${g.sector}",${g.voice_demand},${g.sanctioned_seats},${-g.supply_gap},"${g.gap_status}"\n`;
        }
        res.setHeader('Content-Type', 'text/csv');
        res.setHeader('Content-Disposition', `attachment; filename=PM_AJAY_Perspective_Plan_${district}.csv`);
        res.send(csv);
        return;
      }

      res.json({
        district,
        exportDate: new Date().toISOString(),
        summary,
      });
    } catch (err) {
      next(err);
    }
  };
}
