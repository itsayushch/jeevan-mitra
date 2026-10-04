import hashlib
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple

from app.core.settings import settings
from app.utils.distance import calculate_distance_km, get_block_coordinates


class AggregationService:
    """
    Builds the district demand-vs-supply matrix for Layer 5 (Claim 2: The
    Planning Loop). Every figure is computed from database queries against
    `demand_records` (anonymised) and `local_opportunities` (worker-verified
    supply). No number is hardcoded or model-generated.

    Supply eligibility (all conditions must hold):
      - verified_by_worker_id IS NOT NULL          (worker-verified)
      - verified_at within OPPORTUNITY_REVIEW_DAYS  (non-stale)
      - batch_end_date >= today                     (batch still running/upcoming)
      - available_seats > 0                         (seats actually available)
      - is_archived = 0                             (non-archived)

    Gap scoring formula (exposed in every API response for audit):
      coverage  = min(verified_seats / demand_count, 1)          [0..1]
      distance_factor = 1 + min(nearest_verified_centre_km, CAP) / CAP
                        (2.0 when no verified centre exists in the district)
      severity  = demand_count * (1 - coverage) * distance_factor

    Privacy: cells with demand_count < K_ANONYMITY_THRESHOLD (k-anonymity,
    default 5) are suppressed - numeric figures are nulled and the cell is
    flagged `suppressed: true`.
    """

    K_ANONYMITY_THRESHOLD = 5
    DISTANCE_CAP_KM = 50.0

    def __init__(
        self,
        conn: sqlite3.Connection,
        review_days: Optional[int] = None,
        k_threshold: Optional[int] = None,
        distance_cap_km: Optional[float] = None,
    ):
        self.conn = conn
        self.review_days = review_days if review_days is not None else settings.OPPORTUNITY_REVIEW_DAYS
        self.k_threshold = k_threshold if k_threshold is not None else self.K_ANONYMITY_THRESHOLD
        self.distance_cap_km = distance_cap_km if distance_cap_km is not None else self.DISTANCE_CAP_KM

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------
    def _fetch_supply(self, district: str) -> List[Dict[str, Any]]:
        """Verified, non-stale, non-archived batches for the district."""
        threshold = (datetime.now(timezone.utc) - timedelta(days=self.review_days)).date().isoformat()
        rows = self.conn.execute("""
            SELECT o.id, o.qualification_id, q.title AS qualification_title, q.nqr_code,
                   o.block, o.centre_or_employer_name, o.available_seats, o.total_seats,
                   o.latitude, o.longitude, o.verified_at, o.batch_end_date
            FROM local_opportunities o
            JOIN qualifications q ON q.id = o.qualification_id
            WHERE LOWER(o.district) = LOWER(?)
              AND o.is_archived = 0
              AND o.verified_by_worker_id IS NOT NULL
              AND substr(o.verified_at, 1, 10) >= ?
              AND o.batch_end_date >= date('now')
              AND o.available_seats > 0
            ORDER BY o.block, o.qualification_id;
        """, (district, threshold)).fetchall()
        return [dict(r) for r in rows]

    def _fetch_demand(self, district: str, period: Optional[str]) -> List[Dict[str, Any]]:
        query = """
            SELECT id, qualification_id, block, mobility_radius_km, had_verified_match, created_at
            FROM demand_records
            WHERE LOWER(district) = LOWER(?)
        """
        params: List[Any] = [district]
        if period:
            query += " AND period = ?"
            params.append(period)
        query += " ORDER BY block, qualification_id;"
        rows = self.conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------
    def score_gap(self, demand_count: int, verified_seats: int, nearest_km: Optional[float]) -> Dict[str, float]:
        """
        severity = demand_count * (1 - coverage) * distance_factor
        coverage = min(verified_seats / demand_count, 1)
        distance_factor = 1 + min(nearest_km, cap) / cap  (2.0 if nearest_km is None)
        """
        coverage = min(verified_seats / demand_count, 1.0) if demand_count > 0 else 1.0
        if nearest_km is None:
            distance_factor = 1.0 + 1.0
        else:
            distance_factor = 1.0 + min(nearest_km, self.distance_cap_km) / self.distance_cap_km
        severity = demand_count * (1.0 - coverage) * distance_factor
        return {
            "coverage": round(coverage, 4),
            "distance_factor": round(distance_factor, 4),
            "severity": round(severity, 2),
        }

    @staticmethod
    def _query_id(*parts: str) -> str:
        """Deterministic query identifier so every figure can be traced back."""
        digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:12]
        return f"qry_{digest}"

    # ------------------------------------------------------------------
    # Matrix
    # ------------------------------------------------------------------
    def get_demand_supply_matrix(self, district: str, period: Optional[str] = None) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        supply = self._fetch_supply(district)
        demand = self._fetch_demand(district, period)

        matrix_query_id = self._query_id(
            "matrix", district, period or "*", str(self.review_days), str(self.k_threshold)
        )

        if not demand:
            return {
                "district": district,
                "period": period,
                "generated_at": now,
                "status": "insufficient_data",
                "message": (
                    f"No anonymised demand records found for district '{district}'"
                    + (f" in period '{period}'." if period else ".")
                ),
                "data_basis": {
                    "demand_records_total": 0,
                    "supply_batches_considered": len(supply),
                    "supply_eligibility_filter": (
                        "verified_by_worker_id IS NOT NULL AND verified_at >= "
                        f"(today - {self.review_days} days) AND batch_end_date >= today "
                        "AND available_seats > 0 AND is_archived = 0"
                    ),
                    "k_anonymity_threshold": self.k_threshold,
                },
                "gap_scoring": self._gap_scoring_block(),
                "query_id": matrix_query_id,
                "matrix": [],
                "metrics": {},
            }

        # Index supply by (block, qualification) and by qualification (district-wide)
        supply_by_cell: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
        supply_by_qual: Dict[str, List[Dict[str, Any]]] = {}
        for row in supply:
            supply_by_cell.setdefault((row["block"], row["qualification_id"]), []).append(row)
            supply_by_qual.setdefault(row["qualification_id"], []).append(row)

        # Group demand by (block, qualification)
        demand_by_cell: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
        for rec in demand:
            demand_by_cell.setdefault((rec["block"], rec["qualification_id"]), []).append(rec)

        qual_titles = {
            row["qualification_id"]: (row["qualification_title"], row["nqr_code"])
            for row in supply
        }
        for rec in demand:
            if rec["qualification_id"] not in qual_titles:
                q = self.conn.execute(
                    "SELECT title, nqr_code FROM qualifications WHERE id = ?;",
                    (rec["qualification_id"],),
                ).fetchone()
                if q:
                    qual_titles[rec["qualification_id"]] = (q["title"], q["nqr_code"])

        cells: List[Dict[str, Any]] = []
        for (block, qual_id), records in sorted(demand_by_cell.items()):
            cell_supply = supply_by_cell.get((block, qual_id), [])
            demand_count = len(records)
            verified_seats = sum(s["available_seats"] for s in cell_supply)
            total_seats = sum(s["total_seats"] for s in cell_supply)

            # Nearest verified centre for this qualification anywhere in the district
            nearest_km: Optional[float] = None
            nearest_name: Optional[str] = None
            block_coords = get_block_coordinates(block)
            for s in supply_by_qual.get(qual_id, []):
                dist = calculate_distance_km(
                    block_coords["lat"], block_coords["lon"], s["latitude"], s["longitude"]
                )
                if nearest_km is None or (dist, s["centre_or_employer_name"], s["id"]) < (
                    nearest_km, nearest_name or "", ""
                ):
                    nearest_km = dist
                    nearest_name = s["centre_or_employer_name"]

            # Share of demand with no verified batch: per demand record, a
            # verified batch covers the record only if it sits in the same
            # block within the record's mobility radius (NULL mobility =
            # any verified batch in the block covers it).
            covered = 0
            for rec in records:
                radius = rec.get("mobility_radius_km")
                if radius is None:
                    if cell_supply:
                        covered += 1
                    continue
                for s in cell_supply:
                    dist = calculate_distance_km(
                        block_coords["lat"], block_coords["lon"], s["latitude"], s["longitude"]
                    )
                    if dist <= radius:
                        covered += 1
                        break
            share_no_batch = round(1.0 - (covered / demand_count), 4) if demand_count else 0.0

            gap = demand_count - verified_seats
            scores = self.score_gap(demand_count, verified_seats, nearest_km)

            supply_batch_ids = sorted(s["id"] for s in cell_supply)
            demand_row_ids = sorted(r["id"] for r in records)
            cell_query_id = self._query_id(
                "cell", district, period or "*", block, qual_id,
                *demand_row_ids, *supply_batch_ids,
            )

            suppressed = demand_count < self.k_threshold
            title, nqr_code = qual_titles.get(qual_id, (qual_id, ""))

            cell = {
                "block": block,
                "qualification_id": qual_id,
                "qualification_title": title,
                "nqr_code": nqr_code,
                "demand_count": None if suppressed else demand_count,
                "verified_seats": None if suppressed else verified_seats,
                "total_seats": None if suppressed else total_seats,
                "gap": None if suppressed else gap,
                "nearest_verified_centre_km": nearest_km,
                "nearest_verified_centre_name": nearest_name,
                "share_of_demand_with_no_verified_batch": None if suppressed else share_no_batch,
                "coverage": None if suppressed else scores["coverage"],
                "distance_factor": None if suppressed else scores["distance_factor"],
                "severity_score": None if suppressed else scores["severity"],
                "suppressed": suppressed,
                "suppression_reason": (
                    f"k-anonymity: demand_count {demand_count} < {self.k_threshold}"
                    if suppressed else None
                ),
                "source": {
                    "query_id": cell_query_id,
                    "demand_row_ids": [] if suppressed else demand_row_ids,
                    "supply_batch_ids": supply_batch_ids,
                },
            }
            cells.append(cell)

        # Rank: non-suppressed cells by severity desc, then block/qualification
        visible = [c for c in cells if not c["suppressed"]]
        visible.sort(key=lambda c: (-c["severity_score"], c["block"], c["qualification_title"]))
        suppressed_cells = [c for c in cells if c["suppressed"]]
        suppressed_cells.sort(key=lambda c: (c["block"], c["qualification_title"]))
        ordered_cells = visible + suppressed_cells

        verified_match_count = sum(1 for r in demand if r["had_verified_match"])
        metrics = {
            "total_demand_records": len(demand),
            "demand_with_verified_match_count": verified_match_count,
            "demand_with_verified_match_share": round(verified_match_count / len(demand), 4),
            "blocks_with_demand": len({r["block"] for r in demand}),
            "qualifications_demanded": len({r["qualification_id"] for r in demand}),
            "suppressed_cell_count": len(suppressed_cells),
            "supply_batches_considered": len(supply),
            "total_unmet_demand": sum(
                c["gap"] for c in visible if c["gap"] is not None and c["gap"] > 0
            ),
        }

        return {
            "district": district,
            "period": period,
            "generated_at": now,
            "status": "ok",
            "data_basis": {
                "demand_records_total": len(demand),
                "supply_batches_considered": len(supply),
                "supply_eligibility_filter": (
                    "verified_by_worker_id IS NOT NULL AND verified_at >= "
                    f"(today - {self.review_days} days) AND batch_end_date >= today "
                    "AND available_seats > 0 AND is_archived = 0"
                ),
                "k_anonymity_threshold": self.k_threshold,
                "distance_cap_km": self.distance_cap_km,
            },
            "gap_scoring": self._gap_scoring_block(),
            "query_id": matrix_query_id,
            "matrix": ordered_cells,
            "metrics": metrics,
        }

    def _gap_scoring_block(self) -> Dict[str, Any]:
        return {
            "formula": (
                "coverage = min(verified_seats / demand_count, 1); "
                "distance_factor = 1 + min(nearest_verified_centre_km, distance_cap_km) / distance_cap_km "
                "(2.0 when no verified centre exists in the district); "
                "severity = demand_count * (1 - coverage) * distance_factor"
            ),
            "distance_cap_km": self.distance_cap_km,
            "k_anonymity_threshold": self.k_threshold,
        }
