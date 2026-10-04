from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class PlanningMetadata(BaseModel):
    data_freshness_at: str
    period_start: str
    period_end: str
    district_id: str
    block_id: Optional[str] = None
    privacy_threshold: int = 5
    suppression_applied: bool = False
    metric_version: str = "v1"


class DemandMetricItem(BaseModel):
    qualification_id: str
    qualification_title: str
    sector: str
    nsqf_level: Optional[int] = None
    profiled_beneficiaries_count: Optional[int] = None
    interest_match_count: Optional[int] = None
    verified_match_count: Optional[int] = None
    requested_worker_support_count: Optional[int] = None
    is_suppressed: bool = False


class DemandReportResponse(BaseModel):
    metadata: PlanningMetadata
    demand: List[DemandMetricItem]
    top_demanded_sectors: List[Dict[str, Any]]


class SupplyMetricItem(BaseModel):
    qualification_id: str
    qualification_title: str
    sector: str
    active_opportunities_count: int
    active_providers_count: int
    total_capacity: int
    available_capacity: int
    enrolled_count: int
    full_opportunities_count: int
    expiring_in_7_days: int
    expiring_in_14_days: int
    expiring_in_30_days: int


class SupplyReportResponse(BaseModel):
    metadata: PlanningMetadata
    supply: List[SupplyMetricItem]
    delivery_mode_distribution: Dict[str, int]
    provider_count: int


class GapMetricItem(BaseModel):
    qualification_id: str
    qualification_title: str
    sector: str
    demand_count: Optional[int] = None
    available_verified_capacity: int
    supply_gap: Optional[int] = None
    gap_status: str  # NO_VERIFIED_SUPPLY, FULL_CAPACITY, CAPACITY_DEFICIT, CAPACITY_BALANCED, CAPACITY_SURPLUS, VERIFICATION_STALE
    last_verified_at: Optional[str] = None
    is_suppressed: bool = False


class GapReportResponse(BaseModel):
    metadata: PlanningMetadata
    gaps: List[GapMetricItem]
    summary_by_status: Dict[str, int]


class ReferralFunnelMetrics(BaseModel):
    verified_matches: Optional[int] = None
    referrals_created: Optional[int] = None
    referred_to_centre: Optional[int] = None
    contacted: Optional[int] = None
    enrolled: Optional[int] = None
    training_started: Optional[int] = None
    completed: Optional[int] = None
    verified_livelihood: Optional[int] = None

    # Conversion percentages (None/null if denominator is 0)
    conversion_match_to_referral_pct: Optional[float] = None
    conversion_referral_to_contact_pct: Optional[float] = None
    conversion_contact_to_enrolment_pct: Optional[float] = None
    conversion_enrolment_to_start_pct: Optional[float] = None
    conversion_start_to_complete_pct: Optional[float] = None
    conversion_complete_to_livelihood_pct: Optional[float] = None

    lost_to_follow_up_count: Optional[int] = None
    beneficiary_declined_count: Optional[int] = None
    rejected_count: Optional[int] = None
    is_suppressed: bool = False


class ReferralFunnelResponse(BaseModel):
    metadata: PlanningMetadata
    funnel: ReferralFunnelMetrics


class OutcomeMetrics(BaseModel):
    verified_training_completion: Optional[int] = None
    verified_wage_employment: Optional[int] = None
    verified_self_employment: Optional[int] = None
    reported_outcomes_pending_verification: Optional[int] = None
    reported_dropouts: Optional[int] = None
    outcome_follow_ups_due: Optional[int] = None
    is_suppressed: bool = False


class OutcomesResponse(BaseModel):
    metadata: PlanningMetadata
    outcomes: OutcomeMetrics


class DataQualityMetrics(BaseModel):
    stale_or_expired_opportunities_count: int
    opportunities_due_reverification_count: int
    overdue_follow_ups_count: int
    outcomes_pending_verification_count: int
    active_opportunities_missing_capacity_count: int
    cases_without_referral_consent_count: int
    language_distribution: Dict[str, Optional[int]] = Field(default_factory=dict)
    opportunity_submissions_by_mode: Dict[str, Optional[int]] = Field(default_factory=dict)
    opportunity_submissions_by_status: Dict[str, Optional[int]] = Field(default_factory=dict)
    explainability_quality: Dict[str, Any] = Field(default_factory=dict)


class DataQualityResponse(BaseModel):
    metadata: PlanningMetadata
    data_quality: DataQualityMetrics


class GeographicCoverageBlockItem(BaseModel):
    block_name: str
    demand_count: Optional[int] = None
    verified_active_opportunities: int
    available_capacity: int
    coverage_status: str  # ADEQUATE, DEFICIT, NO_VERIFIED_SUPPLY
    is_suppressed: bool = False


class GeographicCoverageResponse(BaseModel):
    metadata: PlanningMetadata
    blocks: List[GeographicCoverageBlockItem]


class PlanningOverviewResponse(BaseModel):
    metadata: PlanningMetadata
    beneficiaries_profiled: Optional[int] = None
    interest_matches: Optional[int] = None
    verified_matches: Optional[int] = None
    active_verified_opportunities: int
    available_verified_capacity: int
    referrals_created: Optional[int] = None
    enrolments: Optional[int] = None
    verified_livelihoods: Optional[int] = None
    planning_supply_gaps: Optional[int] = None
    is_suppressed: bool = False
    narrative_brief: str


class SnapshotCreateRequest(BaseModel):
    district_id: str
    block_id: Optional[str] = None
    period_start: str
    period_end: str
    notes: Optional[str] = None


class SnapshotReviewRequest(BaseModel):
    notes: Optional[str] = None


class SnapshotApproveRequest(BaseModel):
    notes: Optional[str] = None


class SnapshotResponse(BaseModel):
    id: str
    district_id: str
    block_id: Optional[str] = None
    period_start: str
    period_end: str
    status: str
    generated_by_user_id: Optional[str] = None
    generated_at: str
    metric_version: str
    data_freshness_at: str
    reviewed_by_user_id: Optional[str] = None
    reviewed_at: Optional[str] = None
    approved_by_user_id: Optional[str] = None
    approved_at: Optional[str] = None
    notes: Optional[str] = None
    aggregation: Dict[str, Any]


class ExportCreateRequest(BaseModel):
    export_type: str = "CSV"  # CSV or PDF
    export_scope: str = "FULL_REPORT"  # OVERVIEW, DEMAND, SUPPLY, GAP, FUNNEL, OUTCOMES, FULL_REPORT


class ExportResponse(BaseModel):
    id: str
    snapshot_id: str
    export_type: str
    export_scope: str
    status: str
    requested_by_user_id: str
    generated_at: Optional[str] = None
    expires_at: Optional[str] = None
    checksum: Optional[str] = None
    download_count: int = 0
    download_url: str
