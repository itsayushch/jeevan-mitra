import csv
import io
import json
import uuid
import hashlib
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, Response
from app.services.planning_aggregation_service import PlanningAggregationService
from app.utils.audit_events import log_audit_event


class PlanningExportService:
    """Service managing controlled, reproducible CSV/PDF exports from immutable snapshots.
    Ensures:
    - Exports are derived ONLY from immutable snapshots.
    - Zero PII, staff-only casework notes, or private contacts.
    - Download access is re-authorized at download time.
    - Full audit logging for request, generation, and download.
    """

    @staticmethod
    def create_export(
        conn: sqlite3.Connection,
        current_user: Dict[str, Any],
        snapshot_id: str,
        export_type: str = "CSV",
        export_scope: str = "FULL_REPORT",
    ) -> Dict[str, Any]:
        export_type = export_type.upper()
        if export_type not in ["CSV", "PDF"]:
            raise HTTPException(status_code=400, detail="Invalid export_type. Must be 'CSV' or 'PDF'")

        snap_row = conn.execute("SELECT * FROM planning_snapshots WHERE id = ?;", (snapshot_id,)).fetchone()
        if not snap_row:
            raise HTTPException(status_code=404, detail="Planning snapshot not found")

        agg_service = PlanningAggregationService(conn)
        agg_service.check_district_scope(current_user, snap_row["district_id"])

        now_dt = datetime.now(timezone.utc)
        now_iso = now_dt.isoformat()
        exp_dt = (now_dt + timedelta(days=7)).isoformat()
        export_id = f"exp_{uuid.uuid4().hex[:12]}"

        snapshot_agg = json.loads(snap_row["aggregation_snapshot_json"] or "{}")

        # Generate export file content
        if export_type == "CSV":
            content = PlanningExportService._generate_csv(snap_row, snapshot_agg, export_scope)
        else:
            content = PlanningExportService._generate_pdf_text(snap_row, snapshot_agg, export_scope)

        checksum = hashlib.sha256(content.encode("utf-8")).hexdigest()

        conn.execute("""
            INSERT INTO planning_exports (
                id, snapshot_id, export_type, export_scope,
                requested_by_user_id, generated_at, expires_at,
                status, file_content, checksum, download_count, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'GENERATED', ?, ?, 0, ?);
        """, (
            export_id, snapshot_id, export_type, export_scope,
            current_user.get("id"), now_iso, exp_dt, content, checksum, now_iso
        ))

        log_audit_event(
            conn,
            actor_id=current_user.get("id"),
            actor_name=current_user.get("name", "Staff"),
            actor_role=current_user.get("role", "staff"),
            action="PLANNING_EXPORT_GENERATED",
            entity_type="planning_export",
            entity_id=export_id,
            old_values=None,
            new_values={"snapshot_id": snapshot_id, "export_type": export_type, "checksum": checksum},
        )

        return {
            "id": export_id,
            "snapshot_id": snapshot_id,
            "export_type": export_type,
            "export_scope": export_scope,
            "status": "GENERATED",
            "requested_by_user_id": current_user.get("id"),
            "generated_at": now_iso,
            "expires_at": exp_dt,
            "checksum": checksum,
            "download_count": 0,
            "download_url": f"/api/v1/planning/exports/{export_id}/download",
        }

    @staticmethod
    def get_export(
        conn: sqlite3.Connection,
        current_user: Dict[str, Any],
        export_id: str,
    ) -> Dict[str, Any]:
        query = """
            SELECT e.*, s.district_id 
            FROM planning_exports e
            JOIN planning_snapshots s ON e.snapshot_id = s.id
            WHERE e.id = ?;
        """
        row = conn.execute(query, (export_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Planning export not found")

        agg_service = PlanningAggregationService(conn)
        agg_service.check_district_scope(current_user, row["district_id"])

        return {
            "id": row["id"],
            "snapshot_id": row["snapshot_id"],
            "export_type": row["export_type"],
            "export_scope": row["export_scope"],
            "status": row["status"],
            "requested_by_user_id": row["requested_by_user_id"],
            "generated_at": row["generated_at"],
            "expires_at": row["expires_at"],
            "checksum": row["checksum"],
            "download_count": row["download_count"],
            "download_url": f"/api/v1/planning/exports/{row['id']}/download",
        }

    @staticmethod
    def list_exports(
        conn: sqlite3.Connection,
        current_user: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        target_dist = current_user.get("district") or current_user.get("assigned_district") or "Moradabad"
        agg_service = PlanningAggregationService(conn)
        agg_service.check_district_scope(current_user, target_dist)

        query = """
            SELECT e.*, s.district_id 
            FROM planning_exports e
            JOIN planning_snapshots s ON e.snapshot_id = s.id
            WHERE s.district_id = ?
            ORDER BY e.created_at DESC;
        """
        rows = conn.execute(query, (target_dist,)).fetchall()

        results = []
        for r in rows:
            results.append({
                "id": r["id"],
                "snapshot_id": r["snapshot_id"],
                "export_type": r["export_type"],
                "export_scope": r["export_scope"],
                "status": r["status"],
                "requested_by_user_id": r["requested_by_user_id"],
                "generated_at": r["generated_at"],
                "expires_at": r["expires_at"],
                "checksum": r["checksum"],
                "download_count": r["download_count"],
                "download_url": f"/api/v1/planning/exports/{r['id']}/download",
            })
        return results

    @staticmethod
    def download_export(
        conn: sqlite3.Connection,
        current_user: Dict[str, Any],
        export_id: str,
    ) -> Response:
        query = """
            SELECT e.*, s.district_id 
            FROM planning_exports e
            JOIN planning_snapshots s ON e.snapshot_id = s.id
            WHERE e.id = ?;
        """
        row = conn.execute(query, (export_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Planning export not found")

        # RE-AUTHORIZE AT DOWNLOAD TIME (CRUCIAL INVARIANT)
        agg_service = PlanningAggregationService(conn)
        agg_service.check_district_scope(current_user, row["district_id"])

        # Check expiry
        now_iso = datetime.now(timezone.utc).isoformat()
        if row["expires_at"] and row["expires_at"] < now_iso:
            conn.execute("UPDATE planning_exports SET status = 'EXPIRED' WHERE id = ?;", (export_id,))
            raise HTTPException(status_code=410, detail="Planning export file has expired")

        # Update download count and audit log
        conn.execute("""
            UPDATE planning_exports
            SET download_count = download_count + 1, last_downloaded_at = ?
            WHERE id = ?;
        """, (now_iso, export_id))

        log_audit_event(
            conn,
            actor_id=current_user.get("id"),
            actor_name=current_user.get("name", "Staff"),
            actor_role=current_user.get("role", "staff"),
            action="PLANNING_EXPORT_DOWNLOADED",
            entity_type="planning_export",
            entity_id=export_id,
            old_values={"download_count": row["download_count"]},
            new_values={"download_count": row["download_count"] + 1, "downloaded_at": now_iso},
        )

        content = row["file_content"] or ""
        export_type = row["export_type"]

        if export_type == "CSV":
            filename = f"JeevanMitra_Planning_{row['district_id']}_{export_id}.csv"
            return Response(
                content=content,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )
        else:
            filename = f"JeevanMitra_Planning_{row['district_id']}_{export_id}.pdf"
            return Response(
                content=content,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )

    @staticmethod
    def _generate_csv(snap_row: Any, agg: Dict[str, Any], scope: str) -> str:
        output = io.StringIO()
        writer = csv.writer(output)

        # Header metadata block
        writer.writerow(["# JeevanMitra 2.0 District Planning Export"])
        writer.writerow(["# Snapshot ID", snap_row["id"]])
        writer.writerow(["# District", snap_row["district_id"]])
        writer.writerow(["# Period", f"{snap_row['period_start']} to {snap_row['period_end']}"])
        writer.writerow(["# Generated At", snap_row["generated_at"]])
        writer.writerow(["# Data Freshness", snap_row["data_freshness_at"]])
        writer.writerow(["# Disclaimer", "Figures are district planning indicators, not admission or job guarantees."])
        writer.writerow(["# Privacy Note", "JeevanMitra applies a minimum cell-size privacy threshold of k = 5. Aggregate cells with fewer than five unique beneficiaries are suppressed and returned as null with is_suppressed = true. This is a privacy safeguard designed to reduce re-identification risk; it is not, by itself, a formal guarantee of anonymity or legal compliance."])
        writer.writerow([])

        # Section 1: Demand vs Supply Gaps
        writer.writerow(["=== SECTION 1: DEMAND VS VERIFIED CAPACITY GAPS ==="])
        writer.writerow([
            "Qualification ID", "Qualification Title", "Sector",
            "Expressed Demand Count", "Verified Available Capacity",
            "Supply Gap", "Gap Status", "Freshness Date"
        ])

        gaps = agg.get("gaps", {}).get("gaps", [])
        for g in gaps:
            dem_str = "SUPPRESSED" if g.get("is_suppressed") else str(g.get("demand_count", 0))
            gap_str = "SUPPRESSED" if g.get("is_suppressed") else str(g.get("supply_gap", 0))
            writer.writerow([
                g.get("qualification_id"),
                g.get("qualification_title"),
                g.get("sector"),
                dem_str,
                g.get("available_verified_capacity", 0),
                gap_str,
                g.get("gap_status"),
                g.get("last_verified_at"),
            ])
        writer.writerow([])

        # Section 2: Referral Funnel
        writer.writerow(["=== SECTION 2: REFERRAL FUNNEL ==="])
        writer.writerow(["Stage", "Count", "Conversion Rate (%)"])
        fn = agg.get("funnel", {}).get("funnel", {})
        is_fn_supp = fn.get("is_suppressed")

        stages = [
            ("1. Verified Match", fn.get("verified_matches"), "-"),
            ("2. Referral Created", fn.get("referrals_created"), fn.get("conversion_match_to_referral_pct")),
            ("3. Field Worker Contacted", fn.get("contacted"), fn.get("conversion_referral_to_contact_pct")),
            ("4. Enrolled in Batch", fn.get("enrolled"), fn.get("conversion_contact_to_enrolment_pct")),
            ("5. Training Started", fn.get("training_started"), fn.get("conversion_enrolment_to_start_pct")),
            ("6. Training Completed", fn.get("completed"), fn.get("conversion_start_to_complete_pct")),
            ("7. Verified Livelihood Outcome", fn.get("verified_livelihood"), fn.get("conversion_complete_to_livelihood_pct")),
        ]
        for st_name, cnt, conv in stages:
            cnt_str = "SUPPRESSED" if is_fn_supp else (str(cnt) if cnt is not None else "N/A")
            conv_str = f"{conv}%" if conv is not None else "N/A"
            writer.writerow([st_name, cnt_str, conv_str])
        writer.writerow([])

        # Section 3: Verified vs Reported Outcomes
        writer.writerow(["=== SECTION 3: PROGRAMME OUTCOMES ==="])
        writer.writerow(["Outcome Metric", "Status", "Count"])
        oc = agg.get("outcomes", {}).get("outcomes", {})
        is_oc_supp = oc.get("is_suppressed")

        out_rows = [
            ("Verified Training Completion", "VERIFIED", oc.get("verified_training_completion")),
            ("Verified Wage Employment", "VERIFIED", oc.get("verified_wage_employment")),
            ("Verified Self-Employment", "VERIFIED", oc.get("verified_self_employment")),
            ("Reported Outcomes Pending Verification", "REPORTED", oc.get("reported_outcomes_pending_verification")),
            ("Reported Dropouts", "REPORTED", oc.get("reported_dropouts")),
        ]
        for title, st, c in out_rows:
            c_str = "SUPPRESSED" if is_oc_supp else (str(c) if c is not None else "0")
            writer.writerow([title, st, c_str])

        # Section 4: Data Quality & System Accessibility
        writer.writerow([])
        writer.writerow(["=== SECTION 4: DATA QUALITY & ACCESSIBILITY METRICS ==="])
        writer.writerow(["Metric Category", "Indicator", "Value"])
        dq = agg.get("data_quality", {}).get("data_quality", {})
        writer.writerow(["Catalogue Integrity", "Stale or Expired Opportunities", dq.get("stale_or_expired_opportunities_count", 0)])
        writer.writerow(["Catalogue Integrity", "Opportunities Due Reverification (<14d)", dq.get("opportunities_due_reverification_count", 0)])
        writer.writerow(["Case Management", "Overdue Case Follow-ups", dq.get("overdue_follow_ups_count", 0)])
        writer.writerow(["Consent Governance", "Cases Without Referral Consent", dq.get("cases_without_referral_consent_count", 0)])

        lang_dist = dq.get("language_distribution", {})
        for lang_code, cnt in lang_dist.items():
            cnt_str = "SUPPRESSED (<5)" if cnt is None else str(cnt)
            writer.writerow(["Language Access", f"Preferred Language [{lang_code}]", cnt_str])

        mode_dist = dq.get("opportunity_submissions_by_mode", {})
        for mode, cnt in mode_dist.items():
            cnt_str = "SUPPRESSED (<5)" if cnt is None else str(cnt)
            writer.writerow(["Opportunity Submissions", f"Channel [{mode.upper()}]", cnt_str])

        expl_q = dq.get("explainability_quality", {})
        writer.writerow(["Explainability", "Recommendations With Confirmed Facts", expl_q.get("recommendations_with_confirmed_facts", 0)])
        writer.writerow(["Explainability", "Template Generated Explanations", expl_q.get("template_count", 0)])
        writer.writerow(["Explainability", "LLM Grounded Explanations", expl_q.get("llm_count", 0)])

        return output.getvalue()

    @staticmethod
    def _generate_pdf_text(snap_row: Any, agg: Dict[str, Any], scope: str) -> str:
        """Generates clean structured text-based PDF/report document containing all metadata and tables."""
        overview = agg.get("overview", {})
        gaps = agg.get("gaps", {}).get("gaps", [])
        fn = agg.get("funnel", {}).get("funnel", {})
        oc = agg.get("outcomes", {}).get("outcomes", {})

        lines = [
            "%PDF-1.4 (JeevanMitra 2.0 District Planning Report)",
            "================================================================================",
            "                 GOVERNMENT OF UTTAR PRADESH",
            "       DISTRICT SKILL DEVELOPMENT & LIVELIHOOD PLANNING REPORT",
            "================================================================================",
            f"District: {snap_row['district_id']} | Period: {snap_row['period_start']} to {snap_row['period_end']}",
            f"Snapshot ID: {snap_row['id']} | Status: {snap_row['status']}",
            f"Generated: {snap_row['generated_at']} | Freshness: {snap_row['data_freshness_at']}",
            "--------------------------------------------------------------------------------",
            "",
            "EXECUTIVE PLANNING BRIEF:",
            f"{overview.get('narrative_brief', 'District demand and verified capacity report.')}",
            "",
            "KEY DISTRICT METRICS:",
            f"  - Beneficiaries Profiled: {overview.get('beneficiaries_profiled', 'N/A')}",
            f"  - Verified Interest Matches: {overview.get('interest_matches', 'N/A')}",
            f"  - Active Verified Opportunities: {overview.get('active_verified_opportunities', 0)}",
            f"  - Available Verified Capacity (Seats): {overview.get('available_verified_capacity', 0)}",
            f"  - Referrals Created: {overview.get('referrals_created', 'N/A')}",
            f"  - Verified Livelihood Outcomes: {overview.get('verified_livelihoods', 'N/A')}",
            "",
            "DEMAND VS VERIFIED CAPACITY GAPS (BY TRADE):",
            "--------------------------------------------------------------------------------",
            f"{'Trade / Qualification':<35} | {'Demand':<8} | {'Seats':<6} | {'Gap':<6} | {'Status'}",
            "--------------------------------------------------------------------------------",
        ]

        for g in gaps[:10]:
            title = (g.get("qualification_title") or "Trade")[:34]
            dem = "SUPPR" if g.get("is_suppressed") else str(g.get("demand_count", 0))
            cap = str(g.get("available_verified_capacity", 0))
            gap = "SUPPR" if g.get("is_suppressed") else str(g.get("supply_gap", 0))
            status = g.get("gap_status", "UNKNOWN")
            lines.append(f"{title:<35} | {dem:<8} | {cap:<6} | {gap:<6} | {status}")

        lines.extend([
            "--------------------------------------------------------------------------------",
            "",
            "REFERRAL & OUTCOME FUNNEL:",
            f"  - Verified Matches: {fn.get('verified_matches', 'N/A')}",
            f"  - Referrals Created: {fn.get('referrals_created', 'N/A')} ({fn.get('conversion_match_to_referral_pct') or 'N/A'}%)",
            f"  - Contacted: {fn.get('contacted', 'N/A')} ({fn.get('conversion_referral_to_contact_pct') or 'N/A'}%)",
            f"  - Enrolled: {fn.get('enrolled', 'N/A')} ({fn.get('conversion_contact_to_enrolment_pct') or 'N/A'}%)",
            f"  - Training Completed: {fn.get('completed', 'N/A')} ({fn.get('conversion_start_to_complete_pct') or 'N/A'}%)",
            f"  - Verified Livelihood: {fn.get('verified_livelihood', 'N/A')} ({fn.get('conversion_complete_to_livelihood_pct') or 'N/A'}%)",
            "",
            "VERIFIED VS REPORTED OUTCOMES:",
            f"  - Verified Wage Employment: {oc.get('verified_wage_employment', 'N/A')}",
            f"  - Verified Self-Employment: {oc.get('verified_self_employment', 'N/A')}",
            "",
            "DATA QUALITY & ACCESSIBILITY METRICS:",
            f"  - Stale / Expired Opportunities: {agg.get('data_quality', {}).get('data_quality', {}).get('stale_or_expired_opportunities_count', 0)}",
            f"  - Opportunities Due Re-verification (<14d): {agg.get('data_quality', {}).get('data_quality', {}).get('opportunities_due_reverification_count', 0)}",
            f"  - Overdue Case Follow-ups: {agg.get('data_quality', {}).get('data_quality', {}).get('overdue_follow_ups_count', 0)}",
            f"  - Active Opportunities Missing Capacity: {agg.get('data_quality', {}).get('data_quality', {}).get('active_opportunities_missing_capacity_count', 0)}",
            f"  - Cases Without Referral Consent: {agg.get('data_quality', {}).get('data_quality', {}).get('cases_without_referral_consent_count', 0)}",
            f"  - Recommendations With Confirmed Facts: {agg.get('data_quality', {}).get('data_quality', {}).get('explainability_quality', {}).get('recommendations_with_confirmed_facts', 0)}",
            f"  - Template Explanations: {agg.get('data_quality', {}).get('data_quality', {}).get('explainability_quality', {}).get('template_count', 0)} | Grounded LLM Explanations: {agg.get('data_quality', {}).get('data_quality', {}).get('explainability_quality', {}).get('llm_count', 0)}",
            "",
            "PRIVACY & SAFEGUARDS DISCLAIMER:",
            "  * This report is designed to support DPDP-aligned practices.",
            "  * Individual PII, staff-only notes, and evidence files are strictly omitted.",
            "  * Figures represent aggregate planning indicators, not admission or job guarantees.",
            "================================================================================",
        ])

        return "\n".join(lines)
