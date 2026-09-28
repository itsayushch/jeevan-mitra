import { PlanningRepository } from '../../repositories/planningRepository.js';
import { TradeDemandSupplyGap } from '../../types/index.js';

export interface DistrictAggregationSummary {
  district: string;
  totalBeneficiaries: number;
  totalVerifiedMatches: number;
  totalSupplyGaps: number;
  gaps: TradeDemandSupplyGap[];
  clusterAlerts: Array<{
    block: string;
    trade: string;
    demand: number;
    nearest_centre_distance_km: number;
    suggested_action: string;
  }>;
}

export class PlanningAggregationService {
  private planningRepo: PlanningRepository;

  constructor(planningRepo?: PlanningRepository) {
    this.planningRepo = planningRepo || new PlanningRepository();
  }

  async aggregateDemandVsCapacity(district: string): Promise<DistrictAggregationSummary> {
    const matrix = await this.planningRepo.getDemandSupplyMatrix(district);
    return {
      district,
      totalBeneficiaries: matrix.totalBeneficiaries,
      totalVerifiedMatches: matrix.totalVerifiedMatches,
      totalSupplyGaps: matrix.totalGaps,
      gaps: matrix.gaps,
      clusterAlerts: matrix.clusterAlerts,
    };
  }
}
