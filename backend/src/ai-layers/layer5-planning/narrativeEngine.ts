import { DistrictAggregationSummary } from './aggregationService.js';
import { PlanningBrief } from '../../types/index.js';

export interface GeneratedPlanningBrief {
  district: string;
  period: string;
  narrativeText: string;
  keyInsights: string[];
  suggestedPolicyActions: string[];
  sourceDataTrace: {
    totalInterviewed: number;
    totalVerified: number;
    unmetDemand: number;
    topDeficitTrades: Array<{ trade: string; demand: number; sanctioned: number; deficit: number }>;
  };
}

export class PlanningNarrativeEngine {
  /**
   * Generates a district-level supply-gap brief for District Collectors & Planning Officers.
   * STRICT GUARDRAIL: Every single number is directly injected from query statistics.
   */
  generateBrief(summary: DistrictAggregationSummary, period: string = 'FY 2026-27'): GeneratedPlanningBrief {
    const { district, totalBeneficiaries, totalVerifiedMatches, totalSupplyGaps, gaps, clusterAlerts } = summary;

    const topDeficits = gaps
      .filter((g) => g.supply_gap > 0)
      .slice(0, 4);

    const topDeficitTrades = topDeficits.map((t) => ({
      trade: t.trade_name,
      demand: t.voice_demand,
      sanctioned: t.sanctioned_seats,
      deficit: t.supply_gap,
    }));

    // Formulate strictly grounded paragraphs
    const p1 = `During ${period}, conversational voice interviews were conducted across ${district}, profiling ${totalBeneficiaries} SC youth. Of these, ${totalVerifiedMatches} candidates were successfully matched with verified, live training seats in the district, while an unmet demand gap of ${totalSupplyGaps} candidate allocations remains unaddressed due to local batch or capacity deficits.`;

    let p2 = `Trade-Level Deficit Analysis: `;
    if (topDeficits.length > 0) {
      const tradeDetails = topDeficits.map((td) => {
        return `"${td.trade_name}" recorded ${td.voice_demand} voice requests against ${td.sanctioned_seats} sanctioned seats (net deficit of -${td.supply_gap} seats, Status: ${td.gap_status})`;
      });
      p2 += tradeDetails.join('; ') + '.';
    } else {
      p2 += `Current training seat supply is largely balanced across existing applicant trades.`;
    }

    let p3 = '';
    if (clusterAlerts.length > 0) {
      const topAlert = clusterAlerts[0];
      p3 = `Geographic Cluster Alert: In Block ${topAlert.block}, ${topAlert.demand} SC youth specifically requested ${topAlert.trade} training; however, the nearest sanctioned centre is approximately ${topAlert.nearest_centre_distance_km} km away. Recommended intervention: ${topAlert.suggested_action}.`;
    } else {
      p3 = `Geographic distribution shows consistent accessibility across major block centres.`;
    }

    const narrativeText = `${p1}\n\n${p2}\n\n${p3}`;

    const keyInsights = [
      `Grassroot demand recorded from ${totalBeneficiaries} voice interviews across district blocks.`,
      `Verified seat match conversion rate stands at ${totalBeneficiaries > 0 ? Math.round((totalVerifiedMatches / totalBeneficiaries) * 100) : 0}%.`,
      topDeficits.length > 0
        ? `Primary supply deficit observed in ${topDeficits[0].trade_name} (-${topDeficits[0].supply_gap} seats).`
        : 'Seat allocations meet current baseline aspirations.',
    ];

    const suggestedPolicyActions: string[] = [];
    for (const alert of clusterAlerts.slice(0, 2)) {
      suggestedPolicyActions.push(
        `Deploy Mobile Training Unit in Block ${alert.block} for ${alert.trade} under GIA Component.`
      );
    }
    for (const td of topDeficits.slice(0, 2)) {
      if (td.sanctioned_seats === 0) {
        suggestedPolicyActions.push(
          `Accredit a local training partner in ${district} for ${td.trade_name} (${td.nqr_code}).`
        );
      } else {
        suggestedPolicyActions.push(
          `Sanction ${Math.min(td.supply_gap, 100)} additional seats for ${td.trade_name} in the upcoming Annual Action Plan.`
        );
      }
    }

    return {
      district,
      period,
      narrativeText,
      keyInsights,
      suggestedPolicyActions,
      sourceDataTrace: {
        totalInterviewed: totalBeneficiaries,
        totalVerified: totalVerifiedMatches,
        unmetDemand: totalSupplyGaps,
        topDeficitTrades,
      },
    };
  }
}
